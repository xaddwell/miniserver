#!/usr/bin/python
#coding:utf-8


class NODE_ERROR:
    OK = 0
    TIMEOUT = 7

class NODE_MSG_TYPE:
    CONNECT     ='01'
    DISCONNECT  ='02'
    DATA        ='03'
    POLL        ='04'
    SEND_OK     ='05'
    ACK         ='06'
    ERROR       ='07'
    NACK        ='08'


class NODE_CMD_TYPE:
    CMD     ='01'