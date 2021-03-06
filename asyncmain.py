import sys, getopt
import time
import ssl
import paho.mqtt.client as mqtt
import argparse
import json

from robot import asynchandler

execute_topic = ""
response_topic = ""
mqttc = None

asynchandler.configure_io()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    print("Subscribing to " + args.execute_topic)
    mqttc.subscribe(execute_topic, args.qos)


def on_message(mqttc, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    commandJson = json.loads(msg.payload)
    print(commandJson)
    asynchandler.handle_wheels(commandJson)


def publish_relay_state():
    status = asynchandler.read_sensors()
    publish_state(json.dumps(status))


def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))


def publish_state(json_state):
    json_state_str = json.dumps(json_state)
    print(json_state_str)
    mqttc.publish(response_topic, json_state_str)


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', required=False, default="m2m.eclipse.org")
    parser.add_argument('-e', '--execute_topic', required=False, default="raspberry/commands",
                        help="By defaukt commands are received in topic: raspberry/commands")
    parser.add_argument('-r', '--response_topic', required=False, default="raspberry/state",
                        help="By defaukt state are published in topic raspberry/commands")
    parser.add_argument('-q', '--qos', required=False, type=int, default=0)
    parser.add_argument('-c', '--clientid', required=False, default=None)
    parser.add_argument('-u', '--username', required=False, default=None)
    parser.add_argument('-d', '--disable-clean-session', default=False, action='store_true',
                        help="disable 'clean session' (sub + msgs not cleared when client disconnects)")
    parser.add_argument('-p', '--password', required=False, default=None)
    parser.add_argument('-P', '--port', required=False, type=int, default=None,
                        help='Defaults to 8883 for TLS or 1883 for non-TLS')
    parser.add_argument('-k', '--keepalive', required=False, type=int, default=60)
    parser.add_argument('-F', '--cacerts', required=False, default=None)
    parser.add_argument('-C', '--certfile', required=False, default=None)
    parser.add_argument('-K', '--keyfile', required=False, default=None)
    parser.add_argument('-s', '--use-tls', action='store_true')
    parser.add_argument('--insecure', action='store_true')
    parser.add_argument('--tls-version', required=False, default=None,
                        help='TLS protocol version, can be one of tlsv1.2 tlsv1.1 or tlsv1\n')

    args, unknown = parser.parse_known_args()

    usetls = args.use_tls

    if args.cacerts:
        usetls = True

    port = args.port
    if port is None:
        if usetls:
            port = 8883
        else:
            port = 1883

    mqttc = mqtt.Client(args.clientid, clean_session=not args.disable_clean_session)

    if usetls:
        if args.tls_version == "tlsv1.2":
            tlsVersion = ssl.PROTOCOL_TLSv1_2
        elif args.tls_version == "tlsv1.1":
            tlsVersion = ssl.PROTOCOL_TLSv1_1
        elif args.tls_version == "tlsv1":
            tlsVersion = ssl.PROTOCOL_TLSv1
        elif args.tls_version is None:
            tlsVersion = None
        else:
            print ("Unknown TLS version - ignoring")
            tlsVersion = None

        if not args.insecure:
            cert_required = ssl.CERT_REQUIRED
            certfile = args.certfile
            keyfile = args.keyfile
        else:
            cert_required = ssl.CERT_NONE
            certfile = None
            keyfile = None
        print (tlsVersion)
        mqttc.tls_set(ca_certs=args.cacerts, certfile=certfile, keyfile=keyfile, cert_reqs=cert_required,
                      tls_version=tlsVersion)

        if args.insecure:
            mqttc.tls_insecure_set(True)

    if args.username or args.password:
        mqttc.username_pw_set(args.username, args.password)

    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_publish = on_publish
    mqttc.on_subscribe = on_subscribe

    execute_topic = args.execute_topic
    response_topic = args.response_topic

    print("Connecting to " + args.host + " port: " + str(port))
    mqttc.connect(args.host, port, args.keepalive)

    mqttc.loop_forever()

def app_shutdown():
    handler.terminate()

# EJEMPLO CMD
# python rf.py -s "a2sq3y7mdrjtom.iot.us-west-2.amazonaws.com" -x 8883 -c "./rootCA.pem" -p "./pythonClient.certificate.pem" -k "./pythonClient.private-key.txt" -e "70feba2e" -r "56a40261"
# python rf.py -H a2sq3y7mdrjtom.iot.us-west-2.amazonaws.com -C pythonClient.certificate.pem -K pythonClient.private-key.txt -e 70feba2e -r 56a40261 --use-tls --tls-version tlsv1.2
# python publisher.py -s a2sq3y7mdrjtom.iot.us-west-2.amazonaws.com -x 8883 -c rootCA.pem -p pythonClient.certificate.pem -k pythonClient.private-key.txt -t 52b2ed20
