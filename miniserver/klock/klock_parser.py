#!/usr/bin/python
#coding:utf-8


from pipe.pipe_node import NODE_MSG_TYPE
from .DevDataParser import DevDataParser
import binascii

klock_profile = '00000068'

def on_klock_message(msg):
    mac = msg[0:12]
    op = msg[12:14]
    return on_klock_decode(mac, op, msg)

def on_klock_decode(mac, op, msg):
    if op == NODE_MSG_TYPE.CONNECT:
        return klock_online_decoder(mac, op)
    elif op == NODE_MSG_TYPE.DISCONNECT:
        return klock_offline_decoder(mac, op)
    elif op == NODE_MSG_TYPE.DATA:
        profile = msg[14:22]
        print("%s %s %s %s" %(mac, op, profile, msg[22:]))
        if profile == klock_profile:
            try:
                return klock_data_decoder(mac, op, profile, msg)
            except IndexError as e:
                return None, None
            
    elif op == NODE_MSG_TYPE.SEND_OK or op == NODE_MSG_TYPE.ACK:
        pass
    elif op == NODE_MSG_TYPE.ERROR:
        pass
    else:
        pass

    return None, None


def klock_online_decoder(mac, op):
    mqdata = {}
    mqdata['type'] = 'DEV_ONLINE_NOTIFY'
    mqdata['data'] = {}
    mqdata['data']['macid'] = mac
    mqdata['data']['msgid'] = 0
    return mqdata, None

def klock_offline_decoder(mac, op):
    mqdata = {}
    mqdata['type'] = 'DEV_OFFLINE_NOTIFY'
    mqdata['data'] = {}
    mqdata['data']['macid'] = mac
    mqdata['data']['msgid'] = 0
    return mqdata, None


def klock_data_decoder(mac, op, profile, msg):
    ret, mqdata, resp, msgid = DevDataParser.DevDecode('', binascii.a2b_hex(msg[22:]), mac)
    print("{} : {} : {} : {}".format(ret, mqdata, resp, msgid))
    if len(mqdata) == 0:
        return None, None
    mqdata['data']['msgid'] = msgid
    sdata = None
    if 0 == resp:
        # if MqttDataProcess.respDevList.has_key(devid):
        #     if MqttDataProcess.respDevList[devid]['msgid'] == msgid:
        #         del MqttDataProcess.respDevList[devid]
        return mqdata, None
    else:
        ret2, sdata = DevDataParser.DevRespEncode(msgid, '%02X'%(resp))
        # print("gack "+sdata)
        #PIPEDataProcess.PIPEDataProcess.PIPESend(devid, sdata)
    return mqdata, mqdata['data']['macid']+"01"+klock_profile+sdata



def MqttCheckMsgTarget(msg):
    try:
        if (msg['type'] == 'GW_HEARTBEAT') or (msg['type'] == 'GW_GET_PIPENET'):
            return 0, 'gateway'
        elif (msg['type'] == 'DEV_CMD') or (msg['type'] == 'DEV_PARAM_SET') or \
        (msg['type'] == 'DEV_PARAM_GET') or (msg['type'] == 'DEV_STATUS_GET'):
            return 0, 'device'
        else:
            return -1, ''
    except :
        return -2, ''

def MqttGetMsgId(msg):
    try:
        if (msg['msgid'] >= 0) and (msg['msgid'] <= 65535):
            return msg['msgid']
        else:
            return -2
    except :
        return -1

def MqttGetMacId(msg):
    """
    从平台发送的消息中获取设备ID
    """        
    try:
        #data = json.loads(msg['data'], encoding='utf-8')
        data = msg['data']
        if data['macid'] != '':
            return 0, data['macid']
        else:
            return -1, ''
    except :
        return -2, ''
    pass

def klock_parser_command(data):

    respErr = {}
    #respErr['gateway_id'] = self.gatewayId
    respErr['type'] = 'error'
    #respErr['version'] = COMMON.MQTT_PROTOCOL_VER
    respErrorCode = 1

    if data['data']['macid'] is None:
        respErr['msgid'] = 0
        respErr['data'] = 'type'
        return respErr, respErrorCode

    ret, tat = MqttCheckMsgTarget(data)
    if ret != 0: #格式错误
        respErr['msgid'] = 0
        respErr['data'] = 'type'
        return respErr, respErrorCode
    msgid = MqttGetMsgId(data)
    if msgid == -1:
        respErr['msgid'] = 0
        respErr['data'] = 'msgid not found'
        return respErr, respErrorCode
    elif msgid == -2:
        respErr['msgid'] = 0
        respErr['data'] = 'msgid error'
        return respErr, respErrorCode

    if tat == 'gateway': #发送给网关的消息
        # ret = GatewayDataParser.GatewayDataParser.GWDecode(self.gatewayId, data, msgid)
        # if  ret != 0: #格式错误
        #     respErr['msgid'] = msgid
        #     respErr['data'] = 'message error'
        #     self.mqttsend(json.dumps(respErr))
        # del mqttRecvList[idx]
        # continue
        return None, respErrorCode
    elif tat == 'device': #发送给设备的消息
        ret, macid = MqttGetMacId(data)
        if ret != 0: #格式错误
            respErr['msgid'] = msgid
            respErr['data'] = 'macid error'
            return respErr, respErrorCode

    ret, sdata = DevDataParser.DevEncode(data, msgid)
    if ret != 0:
        respErr['msgid'] = msgid
        respErr['data'] = 'param error'
        return respErr, respErrorCode

    return data['data']['macid']+"01"+klock_profile+sdata, 0
