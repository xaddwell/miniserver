#!/usr/bin/python
#coding:utf-8

#import json
#import logging
#import binascii
#import struct
#import RedisCli
#import COMMON
import re
#import updateFW
#from __builtin__ import False

DEV_CMD_CTRL_ARM = '\x01'
DEV_CMD_CTRL_BEEP = '\x02'
DEV_CMD_GET_STATUS = '\x11'
DEV_CMD_GET_PARAM = '\x12'
DEV_CMD_GET_FUNC = '\x13'
DEV_CMD_SET_PARAM = '\x22'
DEV_CMD_SET_FUNC = '\x23'
DEV_CMD_SET_PWD = '\x31'
DEV_CMD_NOTIFY_FAULT = '\x0D'
DEV_CMD_NOTIFY_CTRL_ARM = '\x0E'
DEV_CMD_NOTIFY_STATUS = '\x0F'
DEV_CMD_NOTIFY_TEMP = '\x51'
DEV_RSP_CTRL_ARM = '\x81'
DEV_RSP_CTRL_BEEP = '\x82'
DEV_RSP_GET_STATUS = '\x91'
DEV_RSP_GET_PARAM = '\x92'
DEV_RSP_GET_FUNC = '\x93'
DEV_RSP_SET_PARAM = '\xA2'
DEV_RSP_SET_FUNC = '\xA3'
DEV_RSP_SET_PWD = '\xB1'
DEV_RSP_NOTIFY_FAULT = '\x8D'
DEV_RSP_NOTIFY_STATUS = '\x8E'
DEV_RSP_NOTIFY_CTRL_ARM = '\x8F'
DEV_RSP_UPDATE = '\xC1'
DEV_RSP_UPDATE_END = '\xC3'

DEV_BYTE_START = 0
DEV_BYTE_CMD = 1
DEV_BYTE_MSGID = 2
DEV_BYTE_LEN = 4
DEV_BYTE_DATA = 5

def CheckSum(data):
    ck = 0
    #for c in data:
    #   ck += ord(c)
    #return chr(ck & 0xFF)
    dlist = re.findall(r'.{2}', data)
    for i in dlist:
        ck += int(i, 16)
    return '%02X'%(ck & 0xFF)
    
class DevDataParser(object):
    def __init__(self):
        pass
    
    @staticmethod
    def DevDecode(gatewayId, msg, macId):
        if msg[DEV_BYTE_START] != '\xFE':
            return False, '', 0, 0
        
        if len(msg) < 5:
            return False, '', 0, 0
        
        strlen = ord(msg[DEV_BYTE_LEN]) + 6
        
        if len(msg) != strlen:
            return False, '', 0, 0
        if len(msg) != strlen:
            return False, '', 0, 0
                
        ck = 0
        for i in range(strlen - 1):
            ck += ord(msg[i])
        
        if (ck & 0xff) != ord(msg[strlen - 1]):
            return False, '', 0, 0
        
        msgid = ord(msg[DEV_BYTE_MSGID])
        msgid <<= 8
        msgid += ord(msg[DEV_BYTE_MSGID + 1])
        mqdata = {}
        # mqdata['version'] = COMMON.MQTT_PROTOCOL_VER
        # mqdata['msgid'] = msgid
        # mqdata['gateway_id'] = gatewayId
        
        resp = -1
        if msg[DEV_BYTE_CMD] == DEV_RSP_CTRL_ARM:
            mqdata['type'] = 'DEV_CMD_RESP'
            mqdata['data'] = DevDataParser.dev_ctrl_arm_resp_process(msg, macId)
            
            resp = 0
        elif msg[DEV_BYTE_CMD] == DEV_RSP_CTRL_BEEP:
            mqdata['type'] = 'DEV_CMD_RESP'
            mqdata['data'] = DevDataParser.dev_ctrl_beep_resp_process(msg, macId)
            
            resp = 0
        elif msg[DEV_BYTE_CMD] == DEV_RSP_GET_STATUS:
            mqdata['type'] = 'DEV_STATUS_GET_RESP'
            mqdata['data'] = DevDataParser.dev_get_status_resp_process(msg, macId)
            resp = 0
        elif msg[DEV_BYTE_CMD] == DEV_RSP_GET_FUNC:
            mqdata['type'] = 'DEV_PARAM_GET_RESP'
            mqdata['data'] = DevDataParser.dev_get_func_resp_process(msg, macId)

            resp = 0
        elif msg[DEV_BYTE_CMD] == DEV_RSP_GET_PARAM:
            mqdata['type'] = 'DEV_PARAM_GET_RESP'
            mqdata['data'] = DevDataParser.dev_get_param_resp_process(msg, macId)
            resp = 0
        elif msg[DEV_BYTE_CMD] == DEV_RSP_SET_PARAM:
            mqdata['type'] = 'DEV_PARAM_SET_RESP'
            mqdata['data'] = DevDataParser.dev_set_param_resp_process(msg, macId)
           
            resp = 0
        elif msg[DEV_BYTE_CMD] == DEV_RSP_SET_FUNC:
            mqdata['type'] = 'DEV_PARAM_SET_RESP'
            mqdata['data'] = DevDataParser.dev_set_func_resp_process(msg, macId)

            resp = 0
        elif msg[DEV_BYTE_CMD] == DEV_RSP_SET_PWD:
            mqdata['type'] = 'DEV_PARAM_SET_RESP'
            mqdata['data'] = DevDataParser.dev_set_pwd_resp_process(msg, macId)
           
            resp = 0
        elif msg[DEV_BYTE_CMD] == DEV_CMD_NOTIFY_STATUS:
            mqdata['type'] = 'DEV_STATUS_NOTIFY'
            mqdata['data'] = DevDataParser.dev_get_status_resp_process(msg, macId)
            
            resp = 0x8f
        elif msg[DEV_BYTE_CMD] == DEV_CMD_NOTIFY_TEMP:
            DevDataParser.dev_notify_temp_process(msg, macId)
            return False, mqdata, 0, msgid
        elif msg[DEV_BYTE_CMD] == DEV_CMD_NOTIFY_CTRL_ARM:
            mqdata['type'] = 'DEV_CMD_RET_RESP'
            mqdata['data'] = DevDataParser.dev_get_status_resp_process(msg, macId)

            resp = 0x8e
        elif msg[DEV_BYTE_CMD] == DEV_CMD_NOTIFY_FAULT:
            mqdata['type'] = 'DEV_FAULT_NOTIFY'
            mqdata['data'] = DevDataParser.dev_get_fault_resp_process(msg, macId)

            resp = 0x8d
        else:
            return False, mqdata, 0, msgid            
        # elif msg[DEV_BYTE_CMD] == DEV_RSP_UPDATE:
        #     logging.info('DEV_RSP_UPDATE')
        #     if msg[DEV_BYTE_DATA] == '\x01':
        #         updateFW.update_req_resp('req_resp_ok')
        #     else:
        #         updateFW.update_req_resp('req_resp_error')
        #     return False, mqdata, 0, msgid
        # elif msg[DEV_BYTE_CMD] == DEV_RSP_UPDATE_END:
        #     logging.info('DEV_RSP_UPDATE_END')
        #     updateFW.update_end_req_resp(msg[DEV_BYTE_DATA], macId)
            
        #     return False, mqdata, 0, msgid
        return True, mqdata, resp, msgid
    
    @staticmethod
    def dev_ctrl_arm_resp_process(msg, macId):
        data = {}
        data['macid'] = macId
        data['option'] = 'arm'
        if msg[DEV_BYTE_DATA] == '\xA1':
            data['result'] = 'ok'
        elif msg[DEV_BYTE_DATA] == '\xA2':
            if msg[DEV_BYTE_DATA+1] == '\xE1':
                data['result'] = 'disable'
            elif msg[DEV_BYTE_DATA+1] == '\xE2':
                data['result'] = 'inuse'
            elif msg[DEV_BYTE_DATA+1] == '\xE3':
                data['result'] = 'position'
            elif msg[DEV_BYTE_DATA+1] == '\xE4':
                data['result'] = 'incorrect'
            else:
                data['result'] = 'error'
        else:
            data['result'] = 'error'
        return data
    
    @staticmethod
    def dev_ctrl_beep_resp_process(msg, macId):
        data = {}
        data['macid'] = macId
        data['option'] = 'beep'
        if msg[DEV_BYTE_DATA] == '\xA1':
            data['result'] = 'ok'
        elif msg[DEV_BYTE_DATA] == '\xA2':
            if msg[DEV_BYTE_DATA+1] == '\xE1':
                data['result'] = 'disable'
            else:
                data['result'] = 'error'
        else:
            data['result'] = 'error'
        return data

    @staticmethod
    def dev_notify_temp_process(msg, macId):
        # RedisCli.SetDevTemp(ord(msg[DEV_BYTE_DATA+3]), macId);
        # logging.info("temp: %s - %d", macId, ord(msg[DEV_BYTE_DATA+3]));
        pass

    @staticmethod
    def dev_get_status_resp_process(msg, macId):
        data = {}
        data['macid'] = macId
        # data['rssi'] = str(RedisCli.GetDevRSSI(macId))
        
        if (ord(msg[DEV_BYTE_DATA]) & 0xF0) == 0x10:
            data['ret'] = 'ok'
        elif (ord(msg[DEV_BYTE_DATA]) & 0xF0) == 0x20:
            data['ret'] = 'error'
        else:
            data['ret'] = 'null'

        if (ord(msg[DEV_BYTE_DATA]) & 0x08) > 0:
            data['mag'] = 'ok'
        else:
            data['mag'] = 'error'
            
        if (ord(msg[DEV_BYTE_DATA]) & 0x04) > 0:
            data['beep'] = 'on'
        else:
            data['beep'] = 'off'

        if (ord(msg[DEV_BYTE_DATA]) & 0x02) > 0:
            data['lock_en'] = 'enable'
        else:
            data['lock_en'] = 'disable'
            
        if (ord(msg[DEV_BYTE_DATA + 1]) & 0xF0) == 0x0:
            data['opcode'] = 'auto'
        elif (ord(msg[DEV_BYTE_DATA + 1]) & 0xF0) == 0x10:
            data['opcode'] = 'server'
        elif (ord(msg[DEV_BYTE_DATA + 1]) & 0xF0) == 0x20:
            data['opcode'] = 'ble'
        elif (ord(msg[DEV_BYTE_DATA + 1]) & 0xF0) == 0x30:
            data['opcode'] = 'leave'
        elif (ord(msg[DEV_BYTE_DATA + 1]) & 0xF0) == 0x40:
            data['opcode'] = 'remote'
        else:
            data['opcode'] = 'unknown'
        
        if (ord(msg[DEV_BYTE_DATA + 1]) & 0xF) == 0x0:
            data['arm'] = 'high'
        elif (ord(msg[DEV_BYTE_DATA + 1]) & 0xF) == 0x1:
            data['arm'] = 'error'
        elif (ord(msg[DEV_BYTE_DATA + 1]) & 0xF) == 0x2:
            data['arm'] = 'mid'
        elif (ord(msg[DEV_BYTE_DATA + 1]) & 0xF) == 0x3:
            data['arm'] = 'low'
        else:
            data['arm'] = 'unknown'

        data['voltage'] = str(ord(msg[DEV_BYTE_DATA + 2])/10.0)+'V'
        data['fw_version'] = str(ord(msg[DEV_BYTE_DATA + 3]))
        data['faultCode'] = ord(msg[DEV_BYTE_DATA + 4])

        # RedisCli.SetDevFW(macId, data['fw_version'])
        # RedisCli.SetDevPos(macId, data['arm'])
        return data

    @staticmethod    
    def dev_get_fault_resp_process(msg, macId):
        data = {}
        data['macid'] = macId
        if (ord(msg[DEV_BYTE_DATA]) & 0x80) == 0x80:
            data['state'] = 'on'
        else:
            data['state'] = 'off'

        cmd = ord(msg[DEV_BYTE_DATA]) & 0x7F
        if cmd == 1:
            data['code'] = 'F300'
        elif cmd == 2:
            data['code'] = 'F100'
        elif cmd == 3:
            data['code'] = 'F200'
        elif cmd == 4:
            data['code'] = 'F201'
        elif cmd == 5:
            data['code'] = 'F202'
        elif cmd == 6:
            data['code'] = 'F400'
        return data           

    @staticmethod
    def dev_get_func_resp_process(msg, macId):
        data = {}
        data['macid'] = macId
        if msg[DEV_BYTE_DATA] == '\x01':
            data['option'] = 'lock_en'
            if msg[DEV_BYTE_DATA + 1] == '\x01':
                data['value'] = 'enable'
            else:
                data['value'] = 'disable'
        elif msg[DEV_BYTE_DATA] == '\x02':
            data['option'] = 'beep_en'
            if msg[DEV_BYTE_DATA + 1] == '\x01':
                data['value'] = 'enable'
            else:
                data['value'] = 'disable'
        elif msg[DEV_BYTE_DATA] == '\x03':
            data['option'] = 'detect_en'
            if msg[DEV_BYTE_DATA + 1] == '\x01':
                data['value'] = 'enable'
            else:
                data['value'] = 'disable'
        elif msg[DEV_BYTE_DATA] == '\x04':
            data['option'] = 'overload_en'
            if msg[DEV_BYTE_DATA + 1] == '\x01':
                data['value'] = 'enable'
            else:
                data['value'] = 'disable'
        elif msg[DEV_BYTE_DATA] == '\x05':
            data['option'] = 'manual_lock_en'
            if msg[DEV_BYTE_DATA + 1] == '\x01':
                data['value'] = 'enable'
            else:
                data['value'] = 'disable'
        elif msg[DEV_BYTE_DATA] == '\x06':
            data['option'] = 'manual_unlock_en'
            if msg[DEV_BYTE_DATA + 1] == '\x01':
                data['value'] = 'enable'
            else:
                data['value'] = 'disable'

        return data

    @staticmethod
    def dev_get_param_resp_process(msg, macId):
        data = {}
        data['macid'] = macId
        if msg[DEV_BYTE_DATA] == '\x08':
            data['option'] = 'temp'
            if msg[DEV_BYTE_DATA + 1] == '\x80':
                data['value'] = '-'
            else:
                data['value'] = ''
            data['value'] += '%d' % ord(msg[DEV_BYTE_DATA + 4])

        return data

    @staticmethod
    def dev_set_param_resp_process(msg, macId):
        pass
    
    @staticmethod
    def dev_set_func_resp_process(msg, macId):
        data = {}
        data['macid'] = macId
        
        if msg[DEV_BYTE_DATA] == '\x01':
            data['option'] = 'lock_en'
        elif msg[DEV_BYTE_DATA] == '\x02':
            data['option'] = 'beep_en'
        elif msg[DEV_BYTE_DATA] == '\x03':
            data['option'] = 'detect_en'
        elif msg[DEV_BYTE_DATA] == '\x04':
            data['option'] = 'overload_en'
        elif msg[DEV_BYTE_DATA] == '\x05':
            data['option'] = 'manual_lock_en'
        elif msg[DEV_BYTE_DATA] == '\x06':
            data['option'] = 'manual_unlock_en'       
        
        if msg[DEV_BYTE_DATA + 1] == '\xA1':
            data['result'] = 'ok'
        elif msg[DEV_BYTE_DATA + 1] == '\xA3':
            data['result'] = 'incorrect'
        else:
            data['result'] = 'error'
            
        return data

    @staticmethod
    def dev_set_pwd_resp_process(msg, macId):
        data = {}
        data['macid'] = macId
        
        if msg[DEV_BYTE_DATA] == '\x01':
            data['option'] = 'master_pwd'
        elif msg[DEV_BYTE_DATA] == '\x02':
            data['option'] = 'guest_pwd'    
        
        if msg[DEV_BYTE_DATA + 1] == '\xA1':
            data['result'] = 'ok'
        elif msg[DEV_BYTE_DATA + 1] == '\xA3':
            data['result'] = 'incorrect'
        else:
            data['result'] = 'error'
            
        return data
    
    @staticmethod
    def DevEncode(msg, msgid):
        code = 'FE'
        mid = '%04X'%(msgid)
        try:
            data = msg['data']
            if msg['type'] == 'DEV_CMD':
                if data['option'] == 'arm':
                    code += '01' + mid + '01'
                    if data['param'] == 'up':
                        code += '01'
                        code += CheckSum(code)
                        return 0, code
                    elif data['param'] == 'down':
                        code += '02'
                        code += CheckSum(code)
                        return 0, code
                    elif data['param'] == 'error':
                        code += '03'
                        code += CheckSum(code)
                        return 0, code
                    elif data['param'] == 'up_immdly':
                        code += '04'
                        code += CheckSum(code)
                        return 0, code
                elif data['option'] == 'beep':
                    code += '02' + mid + '02'
                    if data['param'] == 'off':
                        code += '0000'
                        code += CheckSum(code)
                        return 0, code
                    elif data['param'][0:3] == 'on-':
                        val = int(data['param'][3::])
                        if (val > 0) and (val < 256):
                            code += '01' + '%02X'%(val)
                            code += CheckSum(code)
                            return 0, code
                    elif data['param'][0:4] == 'ons-':
                        val = int(data['param'][4::])
                        if (val > 0) and (val < 256):
                            code += '03' + '%02X'%(val)
                            code += CheckSum(code)
                            return 0, code
                    elif data['param'][0:4] == 'onl-':
                        val = int(data['param'][4::])
                        if (val > 0) and (val < 256):
                            code += '02' + '%02X'%(val)
                            code += CheckSum(code)
                            return 0, code
            elif msg['type'] == 'DEV_PARAM_SET':
                if data['option'] == 'master_pwd':
                    if 6 == len(data['value']):
                        val = int(data['value'], 16)
                        code += '31' + mid + '0401' + \
                        '%06X'%(val)
                        code += CheckSum(code)
                        return 0, code
                elif data['option'] == 'guest_pwd':
                    if 6 == len(data['value']):
                        val = int(data['value'], 16)
                        code += '31' + mid + '0402' + \
                        '%06X'%(val)
                        code += CheckSum(code)
                        return 0, code
                elif data['option'] == 'lock_en':
                    code += '23' + mid + '0201'
                    if data['value'] == 'enable':
                        code += '01'
                    elif data['value'] == 'disable':
                        code += '02'
                    else:
                        return -8, ''
                    code += CheckSum(code)
                    return 0, code
                    
                elif data['option'] == 'beep_en':
                    code += '23' + mid + '0202'
                    if data['value'] == 'enable':
                        code += '01'
                    elif data['value'] == 'disable':
                        code += '02'
                    else:
                        return -7, ''
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'detect_en':
                    code += '23' + mid + '0203'
                    if data['value'] == 'enable':
                        code += '01'
                    elif data['value'] == 'disable':
                        code += '02'
                    else:
                        return -6, ''
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'overload_en':
                    code += '23' + mid + '0204'
                    if data['value'] == 'enable':
                        code += '01'
                    elif data['value'] == 'disable':
                        code += '02'
                    else:
                        return -5, ''
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'manual_lock_en':
                    code += '23' + mid + '0205'
                    if data['value'] == 'enable':
                        code += '01'
                    elif data['value'] == 'disable':
                        code += '02'
                    else:
                        return -4, ''
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'manual_unlock_en':
                    code += '23' + mid + '0206'
                    if data['value'] == 'enable':
                        code += '01'
                    elif data['value'] == 'disable':
                        code += '02'
                    else:
                        return -3, ''
                    code += CheckSum(code)
                    return 0, code
            elif msg['type'] == 'DEV_PARAM_GET':
                if data['option'] == 'lock_en':
                    code += '13' + mid + '0101'
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'beep_en':
                    code += '13' + mid + '0102'
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'detect_en':
                    code += '13' + mid + '0103'
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'overload_en':
                    code += '13' + mid + '0104'
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'manual_lock_en':
                    code += '13' + mid + '0105'
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'manual_unlock_en':
                    code += '13' + mid + '0106'
                    code += CheckSum(code)
                    return 0, code
                elif data['option'] == 'temp':
                    code += '12' + mid + '0108'
                    code += CheckSum(code)
                    return 0, code

            elif msg['type'] == 'DEV_STATUS_GET': 
                code += '11' + mid + '00'
                code += CheckSum(code)
                return 0, code
            
            return -1, '' 
        except :
            return -2, ''

    @staticmethod
    def DevRespEncode(msgid, cmd):
        code = 'FE'
        mid = '%04X'%(msgid)
        code += cmd + mid + '00'
        code += CheckSum(code)
        return 0, code
        
        