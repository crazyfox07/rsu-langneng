from pprint import pprint


class CommandReceiveSet(object):
    """
    指令接收集合
    """
    def __init__(self):
        self.info_b0 = dict()  # 设备状态信息帧-b0
        self.info_b2 = dict()  # 电子标签信息帧
        self.info_b3 = dict()  # 设备车辆信息帧
        self.info_b4 = dict()  # 速通卡信息帧
        self.info_b5 = dict()  # 交易信息帧

    def parse_b0(self, b0):
        """
        解析设备状态信息帧-b0
        :param b0: 设备状态信息帧-b0
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        # b0 = b0.replace('fe01', 'ff').replace('fe00', 'fe')
        self.info_b0['RSCTL'] = b0[4: 6]  # 数据帧序列号
        self.info_b0['FrameType'] = b0[6: 8]  # 数据帧类型标识
        self.info_b0['RSUStatus'] = b0[8: 10]  # ETC天线主状态参数：0x00表示正常，否则表示异常
        self.info_b0['PSAMNum'] = b0[10: 12]  # PSAM卡个数
        self.info_b0['RSUTerminalID1'] = b0[12: 24]  # PSAM卡1终端机编号
        self.info_b0['RSUTerminalID2'] = b0[24: 36]  # PSAM卡2终端机编号
        self.info_b0['RSUAlgld'] = b0[36: 38]  #  算法标识， 默认填写 0x00
        self.info_b0['RSUManuID'] = b0[38: 40]  # RSU厂商代码，16进制表示
        self.info_b0['RSUID'] = b0[40: 46]  # RSU编号，16进制表示
        self.info_b0['RSUVersion'] = b0[46: 50]  # ETC天线软件版本号，16进制表示
        self.info_b0['Reserved'] = b0[50: 60]  # 保留字节
        self.info_b0['BCC'] = b0[60: 62]  # 异或校验值
        return self.info_b0

    def parse_b2(self, b2):
        """
        解析电子标签信息帧-b2
        :param b2: 电子标签信息帧-b2
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        b2 = b2.replace('fe01', 'ff').replace('fe00', 'fe')
        self.info_b2['RSCTL'] = b2[4: 6]  # 数据帧序列号
        self.info_b2['FrameType'] = b2[6: 8]  # 数据帧类型标识
        self.info_b2['OBUID'] = b2[8: 16]  # 电子标签MAC
        self.info_b2['ErrorCode'] = b2[16: 18]  # 状态执行码，取值为"00"有后续数据
        self.info_b2['IssuerIdentifier'] = b2[18: 34]  # 发行商代码
        self.info_b2['SerialNumber'] = b2[34: 50]  # 合同序列号
        self.info_b2['DataOfIssue'] = b2[50: 58]  # 启用日期
        self.info_b2['DataOfExpire'] = b2[58: 66]  # 过期日期
        self.info_b2['EquitmentCV'] = b2[66: 68]  # 设备类型及版本
        self.info_b2['OBUStatus'] = b2[68: 72]  # OBU状态
        self.info_b2['BCC'] = b2[72: 74]  # 异或校验值
        return self.info_b2

    def parse_b3(self, b3):
        """
        解析车辆信息帧-b3
        :param b3: 设备车辆信息帧-b3
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        b3 = b3.replace('fe01', 'ff').replace('fe00', 'fe')
        self.info_b3['RSCTL'] = b3[4: 6]  # 数据帧序列号
        self.info_b3['FrameType'] = b3[6: 8]  # 数据帧类型标识
        self.info_b3['OBUID'] = b3[8: 16]  # 电子标签MAC地址
        self.info_b3['ErrorCode'] = b3[16: 18]  # 状态执行码，取值为"00"正常
        self.info_b3['VehicleLicencePlateNumber'] = b3[18: 42]  # 电子标签记载的车牌号
        self.info_b3['VehicleLicencePlateColor'] = b3[42: 46]  # 车牌颜色
        self.info_b3['VehicleClass'] = b3[46: 48]  # 车辆类型
        self.info_b3['VehicleUserType'] = b3[48: 50]  # 车辆用户类型
        self.info_b3['BCC'] = b3[50: 52]  # 异或校验值
        return self.info_b3

    # TODO 字节不匹配，待确认
    def parse_b4(self, b4):
        """
        解析速通卡信息帧-b4
        :param b4: 速通卡信息帧-b4
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        # b4 = b4.replace('fe01', 'ff').replace('fe00', 'fe')
        self.info_b4['RSCTL'] = b4[4: 6]  # 数据帧序列号
        self.info_b4['FrameType'] = b4[6: 8]  # 数据帧类型标识
        self.info_b4['OBUID'] = b4[8: 16]  # 电子标签MAC地址
        self.info_b4['ErrorCode'] = b4[16: 18]  # 状态执行码，取值为"00"正常
        self.info_b4['CardType'] = b4[18: 20]  # 卡类型（00-速通卡， 其他-保留）
        self.info_b4['PhysicalCardType'] = b4[20: 22]  # 物理卡类型（00-速通卡，其他保留--）
        self.info_b4['TransType'] = b4[22: 24]  # 交易类型（00-传统交易，10-复合交易）
        self.info_b4['CardRestMoney'] = b4[24: 32]  # 卡余额，高位在前，地位在后；【储值记账卡均宜填入实际钱包金额】
        self.info_b4['CardID'] = b4[32: 40]  # 非接触卡片UID(速通卡可以没有，暂填0)
        self.info_b4['IssuerInfo'] = b4[40: 126]  # 卡片发行信息（速通卡0015文件内容）
        self.info_b4['LastStation'] = b4[126: 204]  # 上次过站信息（0012文件或0019文件内容）
        # TODO [204: 212]信息有待确认 文档解释 批注[zbh16]: 未包含二版密钥卡片保留的4字节
        self.info_b4['aaaaaaaaaaa'] = b4[204: 212]
        self.info_b4['BCC'] = b4[212: 214]  # 异或校验值
        return self.info_b4

    def parse_b5(self, b5):
        """
        解析交易信息帧-b5
        :param b4: 交易信息帧-b5
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        # b5 = b5.replace('fe01', 'ff').replace('fe00', 'fe')
        self.info_b5['RSCTL'] = b5[4: 6]  # 数据帧序列号
        self.info_b5['FrameType'] = b5[6: 8]  # 数据帧类型标识
        self.info_b5['OBUID'] = b5[8: 16]  # 电子标签MAC地址
        self.info_b5['ErrorCode'] = b5[16: 18]  # 状态执行码，取值为"00"正常
        self.info_b5['WrFileTime'] = b5[18: 26]  # 交易时间（unix时间）
        self.info_b5['PSAMNo'] = b5[26: 38]  # PSAM卡终端机编号
        self.info_b5['TransTime'] = b5[38: 52]  # 交易时间，格式：YYYYMMDDhhmmss
        self.info_b5['TransType'] = b5[52: 54]  # 交易类型（09-复合消费；06-储值卡传统消费；16-记账卡传统消费）
        self.info_b5['TAC'] = b5[54: 62]  # 交易认证码
        self.info_b5['ICCPaySerial'] = b5[62: 66]  # 速通卡脱机交易序号，对于不涉及消费的交易填充0
        self.info_b5['PSAMTransSerial'] = b5[66: 74]  # PSAM卡终端交易序号
        self.info_b5['CardBalance'] = b5[74: 82]  # 交易后余额，高字节在前
        self.info_b5['BCC'] = b5[82: 84]  # 异或校验值
        return self.info_b5

    def print_obu_info(self):
        print('===================================================')
        pprint(self.info_b0)
        print('===================================================')
        pprint(self.info_b2)
        print('===================================================')
        pprint(self.info_b3)
        print('===================================================')
        pprint(self.info_b4)
        print('===================================================')
        pprint(self.info_b5)

    def clear_info_b2345(self):
        """
        清空收集到的b2, b3, b4, b5指令
        :return:
        """
        self.info_b2.clear()
        self.info_b3.clear()
        self.info_b4.clear()
        self.info_b5.clear()


if __name__ == '__main__':
    command_reiv_set = CommandReceiveSet()
    command_reiv_set.parse_b5('ffff48b56a81353e005f4797743737373737372020082711222809613c67b60012000000110000270f7cff')
    pprint(command_reiv_set.info_b5)

    command_reiv_set.parse_b3('ffff58b363f6b6fe00c2b34c3930313530000000000000010037ff')
    pprint(command_reiv_set.info_b3)