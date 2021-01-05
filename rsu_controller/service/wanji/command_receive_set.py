#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:command_receive_set.py
@time:2020/12/30
"""
from pprint import pprint


class CommandReceiveSet(object):
    def __init__(self):
        self.info_b0 = dict()  # 设备状态信息帧-b0
        self.info_b1 = dict()  # 心跳信息帧

        self.info_b2 = dict()  # 电子标签信息帧
        self.info_b3 = dict()  # 设备车辆信息帧
        self.info_b4 = dict()  # 速通卡信息帧
        self.info_b5 = dict()  # 交易信息帧

    def parse_b0(self, b0):
        """
        设备状态信息帧
        """
        self.info_b0['FrameType'] = b0[16: 18]  # 数据帧类型标识，此处取值B0
        self.info_b0['RSUStatus'] = b0[18: 20]  #
        self.info_b0['PSAMNum'] = b0[20: 22]  #
        self.info_b0['PSAMInfo'] = b0[22: 40]  #
        self.info_b0['RSUAlgId'] = b0[40: 42]  #
        self.info_b0['RSUManuID'] = b0[42: 44]  #
        self.info_b0['RSUID'] = b0[44: 50]  #
        self.info_b0['RSUVersion'] = b0[50: 54]  #
        self.info_b0['workstatus'] = b0[54: 56]  #
        self.info_b0['FlagID'] = b0[56: 62]  #
        self.info_b0['Reserved'] = b0[62: 70]  #
        return self.info_b0

    def parse_b1(self, b1):
        """
        心跳信息帧
        """
        self.info_b1['FrameType'] = b1[16: 18]  # 数据帧类型标识，此处取值B1
        self.info_b1['RSUControlStatus1'] = b1[18: 20]  # 路侧单元控制器1状态 00H：主机 +正常， 01主机 +异常
        self.info_b1['RSUControlStatus2'] = b1[20: 22]  # 预留，默认11H
        self.info_b1['RSUControlStatus3'] = b1[22: 24]  # 预留，默认01H
        self.info_b1['PSAMNum1'] = b1[24: 26]  # 路侧单元控制器1 PSAM数量 记为 n
        self.info_b1['PSAMStatus1'] = b1[26: 32]  # 1字节 PSAM通道号； 1字节 PSAM状态 00H正常， 01H异常 1字节 PSAM卡授权状态， ，00H已授权 01 H未授权 （含授权失败
        self.info_b1['PSAMNum2'] = b1[32: 34]  # 路侧单元控制器 2 PSAM数量 记为 m（默认 0
        self.info_b1['PSAMStatus2'] = ''  # 路侧单元未进行冗余备份时（只有一套设备）PSAMStatus2字段置空
        self.info_b1['AntennaNum'] = b1[34: 36]  # 路侧单元数量 记 为 h，默认 1
        self.info_b1['Reserved'] = b1[36: 38]  # 默认0
        self.info_b1['AntennaStatus'] = b1[38: 46]  # 路侧单元天线 状态 信息
        return self.info_b1

    def parse_b2(self, b2):
        """
        车载单元信息帧
        """
        self.info_b2['FrameType'] = b2[16: 18]  # 数据帧类型标识，此处取值B2
        self.info_b2['OBUID'] = b2[18: 26]  #
        self.info_b2['ErrorCode'] = b2[26: 28]  # 执行状态代码，取值为“00H”时有后续数据
        self.info_b2['AntennaID'] = b2[28: 30]  #
        self.info_b2['DeviceType'] = b2[30: 32]  # 01H为双片式 OBU 02H为单片式OBU
        self.info_b2['IssuerIdentifier'] = b2[32: 48]  # 发行商代码
        self.info_b2['ContractType'] = b2[48: 50]  #
        self.info_b2['ContractVersion'] = b2[50: 52]  #
        self.info_b2['SerialNumber'] = b2[52: 68]  #
        self.info_b2['DateofIssue'] = b2[68: 76]  # OBU合同签署日期
        self.info_b2['DateofExpire'] = b2[76: 84]  # OBU合同过期日期
        self.info_b2['EquitmentCV'] = b2[84: 86]  #
        self.info_b2['OBUStatus'] = b2[86: 90]  # OBU状态
        return self.info_b2

    def parse_b4(self, b4):
        """
        用户信息帧
        """
        self.info_b4['FrameType'] = b4[16: 18]  # 数据帧类型标识，此处取值B4
        self.info_b4['OBUID'] = b4[18: 26]  #
        self.info_b4['ErrorCode'] = b4[26: 28]  # 执行状态代码
        self.info_b4['TransType'] = b4[28: 30]  # 交易类型（10H：复合交易
        self.info_b4['VehicleInfo'] = b4[30: 188]  # 车辆信息文件，读取前 79字节
        self.info_b4['CardRestMoney'] = b4[188: 196]  # 电子钱包文件
        self.info_b4['IssuerInfo'] = b4[196: 296]  # 卡片发行信息（ 0015文件）非 无 数据返回时填充 00H
        self.info_b4['LastStation'] = b4[296: 382]  # 出入口信息 双片式 OBU为 0019文件 无 数据返回时填充 00H
        return self.info_b4

    def parse_b5(self, b5):
        """
        交易信息帧
        """
        self.info_b5['FrameType'] = b5[16: 18]  # 数据帧类型标识，此处取值B8
        self.info_b5['OBUID'] = b5[18: 26]  #
        self.info_b5['ErrorCode'] = b5[26: 28]  # 执行状态代码
        self.info_b5['PSAMNo'] = b5[28: 40]  # PSAM卡终端机编号
        self.info_b5['TransTime'] = b5[40: 54]  # 交易时间，
        self.info_b5['TransType'] = b5[54: 56]  # 交易类型
        self.info_b5['AlgFlag'] = b5[56: 58]  # 算法标识
        self.info_b5['KeyVersion'] = b5[58: 60]  # 消费密钥版本号
        self.info_b5['TAC'] = b5[60: 68]  # 交易认证码
        self.info_b5['ICCPayserial'] = b5[68: 72]  # CPU用户卡脱机交易序号
        self.info_b5['PSAMTransSerial'] = b5[72: 80]  # PSAM卡终端交易序号
        self.info_b5['CardBalance'] = b5[80: 88]  # 交易后余额
        return self.info_b5

    def parse_b8(self, b8):
        """
        TAC信息帧
        """
        self.info_b8['FrameType'] = b8[16: 18]  # 数据帧类型标识，此处取值B8

    def parse_ba(self, ba):
        """
        PSAM初始化 信息帧
        """
        self.info_ba['FrameType'] = ba[16: 18]  # 数据帧类型标识，此处取值B8

    def parse_bb(self, bb):
        """
        PSAM授权信息帧
        """
        self.info_bb['FrameType'] = bb[16: 18]  # 数据帧类型标识，此处取值B8

    def clear_info_b12345(self):
        """
        清空收集到的b2, b3, b4, b5指令
        :return:
        """
        self.info_b1.clear()
        self.info_b2.clear()
        self.info_b3.clear()
        self.info_b4.clear()
        self.info_b5.clear()



if __name__ == '__main__':
    command_receive_set = CommandReceiveSet()
    b0 = 'ffff00050000001bb0000003010101370004727f0008000829200900000000000000009e53'
    pprint(command_receive_set.parse_b0(b0))
    # b0 = 'ffff00070000001bb0000003010101370004727f00080000002009000000000000000071ca'
    # pprint(command_receive_set.parse_b0(b0))
    # b1 = 'ffff00010000000fb10011010003000100010001000002d5dc'
    # pprint(command_receive_set.parse_b1(b1))
    # b2 = 'ffff000200000025b2652bc7a3000101c9bdb6ab370100010100370101202310915520201124203011241020011ae3'
    # pprint(command_receive_set.parse_b2(b2))
    # b4 = 'ffff0007000000b7b4652bc7a30010c2b34c3731523836000000000000010000431714040200260000050000007d5fbfbcd10864e0b0f73c107100000000000000000000000000000d6b0000000000000000000000007a983d0a0332f56dfa0a1e33c9bdb6ab370100011710370119012302112251282020112420301124c2b34c37315238360000000000000100000000000000aa2900c3b5d1269fc842345b0e5e089628000e54e0cdf2bcafcdf2bcaf1601110100000000000000072020e5cb'
    # pprint(command_receive_set.parse_b4(b4))
    # b5 = 'ffff000900000024b5652bc7a30001370004727f20210104171356090001570bf7dc003f00000023fa0a1dcfb5bc'
    # pprint(command_receive_set.parse_b5(b5))