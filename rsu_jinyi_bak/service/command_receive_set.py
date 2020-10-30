from pprint import pprint


class CommandReceiveSet(object):
    """
    指令接收集合
    """

    def __init__(self):
        self.info_b0 = dict()  # rsu设备状态信息
        self.info_b2 = dict()  # RSU设备心跳信息，表示设备是否正常运行
        # self.info_b3 = dict()  # 设备车辆信息帧
        self.info_b4 = dict()  # 车辆相关信息帧
        self.info_b5 = dict()  # 交易信息帧
        self.info_ba = dict()  # PSAM授权初始化信息帧
        self.info_bb = dict()  # PSAM授权信息帧#

    def parse_b0(self, b0):
        """
        解析设备状态信息帧-b0
        :param b0: 设备状态信息帧-b0
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        # b0 = b0.replace('fe01', 'ff').replace('fe00', 'fe')
        self.info_b0['DataLen'] = b0[4:8]  # 数据帧长度
        self.info_b0['FrameType'] = b0[8: 10]  # 数据帧类型标识
        self.info_b0['RSUStatus'] = b0[10: 12]  # ETC天线主状态参数：0x00表示正常，0x02：PSAM卡初始化失败或无卡
        self.info_b0['RSUManuID'] = b0[12: 14]  # RSU厂商代码，16进制表示
        self.info_b0['RSUID'] = b0[14: 20]  # RSU编号，16进制表示
        self.info_b0['SoftVersion'] = b0[20: 24]  # RSU软件版本号
        self.info_b0['HardVersion'] = b0[24: 18]  # RSU硬件版本号
        self.info_b0['ProtocolVersion'] = b0[28: 32]  # 协议版本号，16进制表示。采用大端模式。第1字节表示小版本号，第2字节高4位表示主版本号，第2字节低4位表示次版本号。
        self.info_b0['PsamAuthStatus'] = b0[32: 34]  # PSAM授权状态: 0正常；1，表示PSAM卡需要授权
        self.info_b0['CRC'] = b0[34: 38]  # crc校验值
        return self.info_b0

    def parse_b2(self, b2):
        """
        RSU设备心跳信息，表示设备是否正常运行
        :param b2: 电子标签信息帧-b2
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        # b2 = b2.replace('fe01', 'ff').replace('fe00', 'fe')
        self.info_b2['DataLen'] = b2[4:8]  # 数据帧长度
        self.info_b2['FrameType'] = b2[8: 10]  # 数据帧类型标识
        self.info_b2['StatusCode'] = b2[10: 12]  # 设备状态码 0—设备正常，非0—设备异常：0x01：射频初始化异常 0x02：PSAM卡初始化异常或无卡
        self.info_b2['RSUSwitch'] = b2[12: 14]  # 天线开关状态：0—关闭，1—打开， 其他值—保留
        self.info_b2['PsamAuthStatus'] = b2[14: 16]  # PSAM授权状态: 0正常；1，表示PSAM卡需要授权
        self.info_b2['CRC'] = b2[16: 20]  # crc校验值
        return self.info_b2

    def parse_b4(self, b4):
        """
        车辆相关信息帧-b4  当双片式标签无卡时，IC卡相关字段无效
        :param b4: 速通卡信息帧-b4
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        # b4 = b4.replace('fe01', 'ff').replace('fe00', 'fe')
        self.info_b4['DataLen'] = b4[4:8]  # 数据帧长度
        self.info_b4['FrameType'] = b4[8: 10]  # 数据帧类型标识
        self.info_b4['ObuID'] = b4[10:18]  # OBU号
        self.info_b4['ObuType'] = b4[18:20]  # 设备类型：1—单片式;2—双片式；其他值—保留
        self.info_b4['ICCExist'] = b4[20:22]  # 双片式标签是否插入IC卡：00H—无卡，01H—插卡；单片式固定填充00H
        self.info_b4['OBUStatus'] = b4[22:24]  # OBU状态，表征是否非法拆卸：00H—正常，01H—非法拆卸
        self.info_b4['SysInfoFile'] = b4[24:76]  # 标签系统信息，格式见附表
        self.info_b4['VehicleFile'] = b4[76:234]  # 车辆信息，格式见附表
        self.info_b4['ICCFile0015'] = b4[234:334]  # 双片式IC卡0015文件信息，格式见附表；单片式OBU填充00
        self.info_b4['CardRestMoney'] = b4[334:342]  # 双片式IC卡余额，大端模式，高位在前，低位在后；单位为分
        self.info_b4['StationInfo'] = b4[342:428]  # 双片式IC卡0019文件信息；单片式：为EF02/EF03文件；
        self.info_b4['BlackListStatus'] = b4[428:430]  # 0：正常 1：属于黑名单车辆 2：属于白名单车辆
        self.info_b4['Reserved'] = b4[430: 556]  # 保留字节。当C0的WorkMode字段值为0x45时，该字段前17字节为密文解密附加信息。解密时，对双片式标签，需要将VehicleFile字段的密文信息和该字段附加信息一共88字节发给PSAM卡或者加密机。对单片式标签，则是全部的96字节。
        self.info_b4['CRC'] = b4[556: 560]  # crc校验值
        # 解析标签系统信息 self.info_b4['SysInfoFile']
        self.info_b4['IssuerIdentifier'] = self.info_b4['SysInfoFile'][:16]  # 发行商代码
        self.info_b4['CompactType'] = self.info_b4['SysInfoFile'][16:18]  # 协约类型
        self.info_b4['CompactVersion'] = self.info_b4['SysInfoFile'][18:20]  # 协约版本
        self.info_b4['ApplySerial'] = self.info_b4['SysInfoFile'][20:36]  # 应用序列号
        self.info_b4['CompactDateSign'] = self.info_b4['SysInfoFile'][36:44]  # 协议签署日期
        self.info_b4['CompactDateExpire'] = self.info_b4['SysInfoFile'][44:52]  # 协议过期日期
        # 解析车辆信息self.info_b4['VehicleFile']
        self.info_b4['VehicleLicencePlateNumberReserved'] = self.info_b4['VehicleFile'][:24]  # 车牌号
        self.info_b4['VehicleLicencePlateColorReserved'] = self.info_b4['VehicleFile'][24:28]  # 车牌颜色
        self.info_b4['VehicleClassReserved'] = self.info_b4['VehicleFile'][28:30]  # 车型
        self.info_b4['VehicleUserTypeReserved'] = self.info_b4['VehicleFile'][30:32]  # 车辆用户类型
        self.info_b4['VehicleSize'] = self.info_b4['VehicleFile'][32:40]  # 车辆尺寸
        self.info_b4['VehicleWheelNum'] = self.info_b4['VehicleFile'][40:42]  # 车轮数
        self.info_b4['VehicleAxleNum'] = self.info_b4['VehicleFile'][42:44]  # 车轴数
        # 解析0015文件 self.info_b4['ICCFile0015']
        self.info_b4['CardIssuerIdentification'] = self.info_b4['ICCFile0015'][:16]  # 发卡方标识
        self.info_b4['CardType'] = self.info_b4['ICCFile0015'][16:18]  # 卡片类型 16 储值卡  17 记账卡
        self.info_b4['CardVersion'] = self.info_b4['ICCFile0015'][18:20]  # 卡片版本号
        self.info_b4['CardNetNo'] = self.info_b4['ICCFile0015'][20:24]  # 卡片网络编号
        self.info_b4['UserCardNo'] = self.info_b4['ICCFile0015'][24:40]  # 用户卡内部编号
        self.info_b4['DataOfIssue'] = self.info_b4['ICCFile0015'][40:48]  # 启用时间
        self.info_b4['DataOfExpire'] = self.info_b4['ICCFile0015'][48:56]  # 到期时间
        self.info_b4['VehicleLicencePlateNumber'] = self.info_b4['ICCFile0015'][56:80]  # 车牌号
        self.info_b4['VehicleUserType'] = self.info_b4['ICCFile0015'][80:82]  # 用户类型
        self.info_b4['VehicleLicencePlateColor'] = self.info_b4['ICCFile0015'][82:84]  # 车牌颜色
        self.info_b4['VehicleClass'] = self.info_b4['ICCFile0015'][84:86]  # 车型
        return self.info_b4

    def parse_b5(self, b5):
        """
        交易信息帧-b5
        :param b5: 交易信息帧-b5
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        self.info_b5['DataLen'] = b5[4:8]  # 数据帧长度
        self.info_b5['FrameType'] = b5[8: 10]  # 数据帧类型标识
        self.info_b5['ObuID'] = b5[10:18]  # OBU号
        self.info_b4['ObuType'] = b5[18:20]  # 设备类型：1—单片式;2—双片式；其他值—保留
        self.info_b5['ErrorCode'] = b5[20:22]  # 执行状态代码：0表示交易成功，其他值表示交易超时或失败：0x01 OBU通信超时 0x02 OBU未插IC卡 0x03 OBU返回的数据异常 0x04 标签报错 0x05 IC卡报错
        self.info_b5['TradeRecord'] = b5[22:150]  # 交易流水记录。执行状态码正常且流水处理方式为0时有意义 非0时，数据无效。
        self.info_b5['CRC'] = b5[150:154]  # crc校验值
        # 交易流水记录（TradeRecord）各字段含义如下
        self.info_b5['CardRestMoney'] = self.info_b5['TradeRecord'][: 8]  # 双片式标签ICC交易后卡片余额；单片式标签填充00；单位为分
        self.info_b5['TransTime'] = self.info_b5['TradeRecord'][8: 22]  # BCD编码格式，yyyyMMddHHmmss 例：20200412201745
        self.info_b5['Keytype'] = self.info_b5['TradeRecord'][22: 24]  # 交易密钥标识：00H—3DES算法，04H—SM4算法
        self.info_b5['PSAMTransSerial'] = self.info_b5['TradeRecord'][24: 32]  # 双片式标签ICC交易PSAM卡计算MAC1返回的交易序号；单片式为全0
        self.info_b5['PsamTerminalID'] = self.info_b5['TradeRecord'][32: 44]  # 终端机编号，PSAM卡编号
        self.info_b5['ETCTradNo'] = self.info_b5['TradeRecord'][44: 48]  # IC卡交易序列号
        self.info_b5['TAC'] = self.info_b5['TradeRecord'][48: 56]  # 交易TAC码
        self.info_b5['ICC_RAND'] = self.info_b5['TradeRecord'][56: 64]  # IC卡消费随机数
        self.info_b5['Reserved'] = self.info_b5['TradeRecord'][64: 128]  # 保留字节
        return self.info_b5

    def parse_ba(self, ba):
        """
        PSAM授权初始化信息帧-ba
        :param ba:
        :return:
        """
        # 接收数据时 'fe01'合并为'ff', 'fe00'合并为'fe'
        self.info_ba['DataLen'] = ba[4: 8]  # 数据帧长度
        self.info_ba['FrameType'] = ba[8: 10]  # 数据帧类型标识
        self.info_ba['ErrorCode'] = ba[10: 12]  # 执行状态，0表示正常；1表示无需授权；其他非0，表示异常
        self.info_ba['PsamTerminalID'] = ba[12: 24]  # 6字节PSAM终端机编号
        self.info_ba['PsamSN'] = ba[24: 44]  # 10字节PSAM序列号
        self.info_ba['KeyType'] = ba[44: 46]  # 1字节PSAM密钥卡类型
        self.info_ba['PsamVersion'] = ba[46: 48]  # 1字节PSAM版本号
        self.info_ba['AreaCode'] = ba[48: 64]  # 8字节PSAM应用区域标识
        self.info_ba['RandomCode'] = ba[64: 80]  # 8字节PSAM随机数(由4个字节有效随机数和4字节0值填充数组成，如果只需要4个字节随机数，取前4字节即可)
        self.info_ba['CRC'] = ba[80: 84]  # crc校验值

    def parse_bb(self, bb):
        """
        PSAM授权信息帧-bb
        :param bb:
        :return:
        """
        self.info_bb['DataLen'] = bb[4: 8]  # 数据帧长度
        self.info_bb['FrameType'] = bb[8: 10]  # 数据帧类型标识
        self.info_bb['ErrorCode'] = bb[10: 12]  # 执行状态，0表示正常；非0，表示异常
        self.info_bb['AuthStatus'] = bb[12: 16]  # 2字节授权状态码(Timecos应答状态码，9000H表示成功，其他值异常)
        self.info_bb['CRC'] = bb[16: 20]  # crc校验值

    def print_obu_info(self):
        print('===================================================')
        pprint(self.info_b0)
        print('===================================================')
        pprint(self.info_b2)
        print('===================================================')
        pprint(self.info_b4)
        print('===================================================')
        pprint(self.info_b5)
        print('===================================================')
        pprint(self.info_ba)
        print('===================================================')
        pprint(self.info_bb)

    def clear_info_b2345(self):
        """
        清空收集到的b2, b3, b4, b5指令
        :return:
        """
        self.info_b0.clear()
        self.info_b2.clear()
        self.info_b4.clear()
        self.info_b5.clear()
        self.info_ba.clear()
        self.info_bb.clear()


if __name__ == '__main__':
    command_reiv_set = CommandReceiveSet()
    command_reiv_set.parse_b0('ffff000db00002fbc3d61000000111060072e5')
    pprint(command_reiv_set.info_b0)

    command_reiv_set.parse_b2('ffff0004b20000008275')
    pprint(command_reiv_set.info_b2)

    command_reiv_set.parse_b4(
        'ffff0112b402f7d593020101b9e3b6ab44010001010286030002200479e1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000bdf0d2e7bdf0d2e71610000000000000000004272019102420241024d4c14131313131310000000001000000000000000000000d8f8eaa2900a1a2a3a4a5a6a7a8a1a2a3a4a5a6a7a8a1a2a3a4a5a6a7a8a1a2a3a4a5a6a7a8a1a2a3a4a5a6a7a800aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa509e')
    pprint(command_reiv_set.info_b4)

    command_reiv_set.parse_b5(
        'ffff0047b502f7d5930200000d8f8b2020102017055600000000700000000005090070ed2e8cdc2765a9a30000000000000000000000000000000000000000000000000000000000000000bd89')
    pprint(command_reiv_set.info_b5)
    # command_reiv_set.parse_b5('ffff48b56a81353e005f4797743737373737372020082711222809613c67b60012000000110000270f7cff')
    # pprint(command_reiv_set.info_b5)
    #
    # command_reiv_set.parse_b3('ffff58b363f6b6fe00c2b34c3930313530000000000000010037ff')
    # pprint(command_reiv_set.info_b3)
