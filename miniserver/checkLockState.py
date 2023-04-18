#!/usr/bin/python
#coding:utf-8

import time
import threading

def check_node_list_command():
    return "smembers nodes"


def check_node_list_message(node_list, publish, topic):
    print("node list: "+str(node_list))
    for node in node_list:
        if len(node) == 12:
            print("check lock " + node)
            publish(topic, node+"0100000068FE1100010010")
            time.sleep(0.05)

