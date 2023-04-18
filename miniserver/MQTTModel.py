#!/usr/bin/python
#coding:utf-8

import paho.mqtt.client as mqtt

MQTT_IP = '121.196.206.137'
MQTT_PORT= 1883

class MQTTModel:

    def __init__(self, on_connect=None, on_disconnect=None, on_message=None):
        self.__on_connect = on_connect
        self.__on_disconnect = on_disconnect
        self.__on_message = on_message

        self.__on_publish=None
        self.__on_subscribe=None
        self.__on_unsubscribe=None

        self.__clientid = None
        self.__username = None
        self.__password = None

    def on(self, on_publish=None, on_subscribe=None, on_unsubscribe=None):
        self.__on_publish=on_publish
        self.__on_subscribe=on_subscribe
        self.__on_unsubscribe=on_unsubscribe

    def auth(self, username=None, password=None, clientid=None):
        self.__clientid = clientid
        self.__username = username
        self.__password = password


    def connect(self, ip=MQTT_IP, port=MQTT_PORT):
        self.__ip = ip
        self.__port = port

        if self.__clientid is None:
            self.__client = mqtt.Client()
        else:
            self.__client = mqtt.Client(client_id=self.__clientid)

        if self.__username is not None and self.__password is not None:
            self.__client.username_pw_set(self.__username, self.__password)

        self.__client.on_connect = self.__on_connect
        self.__client.on_disconnect = self.__on_disconnect
        self.__client.on_message = self.__on_message

        self.__client.on_publish = self.__on_publish
        self.__client.on_subscribe = self.__on_subscribe
        self.__client.on_unsubscribe = self.__on_unsubscribe
        
        self.__client.connect(self.__ip, self.__port, 60)

    def publish(self, topic, data, qos=2):
        return self.__client.publish(topic, data, qos)

    def subscribe(self, topic, qos):
        self.__client.subscribe(topic, qos)

    def start(self):
        self.__client.loop_start()

    def stop(self):
        self.__client.loop_stop()
        self.__client.disconnect()

    def process(self):
        pass

    
if __name__ == "__main__":
    import time
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code: " + str(rc))

    def on_disconnect(client, userdata, flags, rc):
        print("Disconnected with result code: " + str(rc))

    def on_message(client, userdata, msg):
        print(msg.topic)
        print(msg.payload)
        
    mq = MQTTModel(on_connect, on_disconnect, on_message)
    mq.auth(username="your username", password='your passord', clientid='your clientid')
    mq.connect()
    mq.subscribe('#', 2)
    mq.start()
    while True:
        time.sleep(1)