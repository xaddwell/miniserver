#!/usr/bin/python
#coding:utf-8

import paho.mqtt.client as mqtt

MQTT_IP = '121.196.206.137'
MQTT_PORT= 1883

class MQTTModel:

    def __init__(self, client_id, on_connect, on_disconnect, on_message):
        self.__on_connect = on_connect
        self.__on_disconnect = on_disconnect
        self.__on_message = on_message

        self.__client = mqtt.Client(client_id=client_id)
        #self.__client = mqtt.Client()

        self.__client.on_connect = self.__on_connect
        self.__client.on_message = self.__on_message

    def connect(self, username=None, password=None, addr=None, port=None):
        self.__client.username_pw_set(username, password)
        self.__client.connect(addr, port, 600)

    def publish(self, topic, data, qos=2):
        self.__client.publish(topic, data, qos)

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
        print(msg.topic + " " + str(msg.payload))
        
    mq = MQTTModel('your clientid', on_connect, on_disconnect, on_message)
    mq.connect(username='your username',
        password='your username',
        addr=MQTT_IP,
        port=1883)
    mq.subscribe('PIPELock/Status/NG102', 2)
    mq.subscribe('PIPELock/set/NG102', 2)
    i = 0
    while True:
        # mq.publish("PIPELock/set/NG102",i)
        i += 1
        time.sleep(1)