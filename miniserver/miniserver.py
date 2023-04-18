#!/usr/bin/python
#coding:utf-8

import getopt
import sys
import time
import re
import json
import socket

try:
    import queue
except ImportError:
    import Queue as queue

from Logger import logger

from MQTTModel import MQTTModel
from klock.klock_parser import on_klock_message, klock_parser_command

from checkLockState import check_node_list_command, check_node_list_message

MINSERVER_SUBSCRIBE_TOPIC   = "PIPELock/set/#"
PUBLISH_PREFIX              = "PIPELock/Status/#"

minigw_list = set()

group_name = "klm-r2mqtt"

class MContext():
    pass

mContent=MContext()
mContent.ap_cmd = None

def on_minigw_node_message(topic, payload):
    ug = topic[18:-13].split("/")
    user = ug[0]
    gw = ug[1]
    pl = payload[:2]
    rssi = eval('0x'+payload[2:4])
    minigw_list.add(gw)

    #logger.logger.debug(minigw_list)
    logger.logger.debug("rssi {} {} gw {} ".format(rssi, user, gw))
    logger.logger.info("on pipe.message "+payload)

    upload, resp = on_klock_message(payload[4:])
    if upload is not None:
        upload['data']['rssi'] = rssi
        upload['gateway_id'] = gw
        upload['msgid'] = upload['data']['msgid']
        upload['version'] = "v1.1"
        logger.logger.debug("upload: "+str(upload))
        miniMQTT.publish("PIPELock/status/"+gw, json.dumps(upload))
    if resp is not None:
        logger.logger.debug("resp "+resp)
        miniServer.publish(PUBLISH_PREFIX+user+"/"+gw+"/pipe/command", resp)


def on_minigw_message(topic, payload):
    if re.match("^klm/iot/minigw/v2/[\w\-]+/[\w\-]+/pipe/message$", topic) is not None:
        on_minigw_node_message(topic, payload)
    elif re.match("^klm/iot/minigw/v2/[\w\-]+/[\w\-]+/pipe/ping$", topic) is not None:
        ug = topic[18:-10].split("/")
        user = ug[0]
        gw = ug[1]
        minigw_list.add(gw)
        #logger.logger.debug(minigw_list)
        connect_tick = eval('0x'+payload[10:].replace("'",""))
        ping_msg = {"gateway_id":gw, "msgid":(connect_tick%65536), "version": "v1.1", "type": "GW_HEARTBEAT_NOTIFY", "data": ""}
        miniMQTT.publish("PIPELock/status/"+gw, json.dumps(ping_msg))
        if connect_tick == 2:
            miniServer.publish(PUBLISH_PREFIX+user+"/"+gw+"/redis/command", check_node_list_command())
            mContent.ap_cmd = check_node_list_command()
    elif re.match("^klm/iot/minigw/v2/[\w\-]+/[\w\-]+/redis/message$", topic) is not None:
        if mContent.ap_cmd is not None:
            print("ap message: "+payload)
            try:
                ug = topic[18:-10].split("/")
                user = ug[0]
                gw = ug[1]
                check_lock_topic = PUBLISH_PREFIX+user+"/"+gw+"/pipe/command"

                def on_public_check_lock_cmd(topic, command):
                    miniServer.publish(topic, command)

                node_list = json.loads(payload)
                check_node_list_message(node_list.values(), on_public_check_lock_cmd, check_lock_topic)
                mContent.ap_cmd = None
            except:
                print("json error")
            

def on_minimqtt_message(topic, payload):
    gw = topic[13:]
    logger.logger.debug("set gw: "+gw)
    if gw in minigw_list:
        data = json.loads(payload, encoding='utf-8')
        lock_cmd, errCode= klock_parser_command(data)
        if lock_cmd is not None:
            if errCode is 0:
                logger.logger.debug("lock "+lock_cmd)
                miniServer.publish("klm/iot/minigw/v2/klm-r2mqtt/"+gw+"/pipe/command", lock_cmd)
            else:
                lock_cmd['gateway_id'] = gw
                lock_cmd['version'] = "v1.1"
                logger.logger.debug("error "+str(lock_cmd))
                miniMQTT.publish("PIPELock/status/"+gw, json.dumps(lock_cmd))



class MINISERVER:

    def __init__(self):
        self.__mqtt = None
        self.mqtt_ip = '121.196.206.137'
        self.mqtt_port = 1883
        self.mqtt_clientid = 'NG102' #this conf for gateway server
        self.mqtt_username = 'NG102'
        self.mqtt_password = ''

    def mqtt_init(self):

        self.__mqtt = MQTTModel(self.on_mqtt_connect, self.on_mqtt_disconnect, self.on_mqtt_message)
        if self.mqtt_clientid is not None and self.mqtt_username is not None and self.mqtt_password is not None:
            self.__mqtt.auth(username=self.mqtt_username, password=self.mqtt_password, clientid=self.mqtt_clientid)
        
    def mqtt_connect(self):
        self.__mqtt.connect(self.mqtt_ip, self.mqtt_port)
        self.__mqtt.start()

    def mqtt_subscribe(self):
        if self.__mqtt is not None:
            self.__mqtt.subscribe(MINSERVER_SUBSCRIBE_TOPIC, 2)

    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        logger.logger.debug("mqtt connect with result code: " + str(rc))
        self.mqtt_subscribe()

    def on_mqtt_disconnect(self, client, userdata, rc):
        logger.logger.debug("mqtt disconnected with result code: " + str(rc))

    def on_mqtt_message(self, client, userdata, msg):
        try:
            logger.logger.debug(msg.topic + " " + str(msg.payload))
        except UnicodeDecodeError:
            logger.logger.debug("msg Error!!!!!!!!!!!")

        on_minigw_message(str(msg.topic), str(msg.payload))

    def publish(self, topic, payload):
        self.__mqtt.publish(topic, payload)

    def loop(self):
        pass

    
class MINIMQTT:

    def __init__(self):
        self.__pub_msg = None
        self.__pub_timeout = 0
        self.__queue = queue.Queue()
        self.__mqtt = None
        self.mqtt_ip = '121.196.206.137'
        self.mqtt_port = 1883
        self.mqtt_clientid = 'NG102' #this conf for api server
        self.mqtt_username = 'kele'
        self.mqtt_password = ''

    def mqtt_init(self):

        self.__mqtt = MQTTModel(self.on_mqtt_connect, self.on_mqtt_disconnect, self.on_mqtt_message)
        self.__mqtt.on(self.on_publish, self.on_subscribe)
        if self.mqtt_clientid is not None and self.mqtt_username is not None and self.mqtt_password is not None:
            self.__mqtt.auth(username=self.mqtt_username, password=self.mqtt_password, clientid=self.mqtt_clientid)
        
    def mqtt_connect(self):
        self.__mqtt.connect(self.mqtt_ip, self.mqtt_port)
        self.__mqtt.start()

    def mqtt_disconnect(self):
        self.__mqtt.stop()

    def mqtt_subscribe(self):
        if self.__mqtt is not None:
            self.__mqtt.subscribe("PIPELock/set/#", 2)

    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        logger.logger.debug("mqtt connect with result code: " + str(rc))
        self.mqtt_subscribe()

    def on_mqtt_disconnect(self, client, userdata, rc):
        logger.logger.debug("mqtt disconnected with result code: " + str(rc))

    def on_mqtt_message(self, client, userdata, msg):
        logger.logger.debug(msg.topic + " " + str(msg.payload))
        on_minimqtt_message(str(msg.topic), str(msg.payload))

    def publish(self, topic, payload):
        logger.logger.debug("queue "+payload)
        # rc = self.__mqtt.publish(topic, payload)
        # logger.logger.debug("mqtt publish "+str(rc))
        self.__queue.put({"t":topic, "p":payload}, block=False)

    def on_publish(self, client, userdata, mid):
        logger.logger.debug("mqtt on publish "+str(mid))
        self.__pub_msg = None

    def on_subscribe(self, client, userdata, mid, granted_qos):
        logger.logger.debug("mqtt on_subscribe "+str(mid))

    def loop(self):
        if self.__pub_msg is None:
            try:
                self.__pub_msg = self.__queue.get(block=False)
                self.__pub_timeout = 0
                logger.logger.debug("mqtt publish "+str(self.__pub_msg))
                rc = self.__mqtt.publish(self.__pub_msg["t"], self.__pub_msg["p"])
                logger.logger.debug("mqtt publish "+str(rc))
            except queue.Empty:
                pass
        else:
            self.__pub_timeout = self.__pub_timeout + 1
            if self.__pub_timeout > 300:
                self.__pub_timeout = 0
                try:
                    logger.logger.debug("mqtt reconnect")
                    self.mqtt_disconnect()
                    time.sleep(1)
                    self.mqtt_init()
                    self.mqtt_connect()
                    logger.logger.debug("mqtt publish first "+str(self.__pub_msg))
                    if self.__pub_msg is not None:
                        rc = self.__mqtt.publish(self.__pub_msg["t"], self.__pub_msg["p"])
                        logger.logger.debug("mqtt publish fist "+str(rc))
                except socket.error as msg:
                    logger.logger.debug("Error: "+str(msg))


miniServer = MINISERVER()
miniMQTT = MINIMQTT()

def main():
    miniServer.mqtt_init()
    miniServer.mqtt_connect()
    # miniMQTT.mqtt_init()
    # miniMQTT.mqtt_connect()
    i = 0
    while True:
        i += 1
        # miniServer.publish("PIPELock/Status/NG102","Server:{}".format(i))
        miniServer.loop()
        # miniMQTT.loop()
        time.sleep(0.01)

if __name__ == "__main__":
    main()
