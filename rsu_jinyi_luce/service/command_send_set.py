# -*- coding: utf-8 -*-

import time

from common.utils import CommonUtil


class CommandSendSet(object):
    """
    指令发送集合
    """

    @staticmethod
    def get_data_len(data):
        """
        计算data的长度，然后转成hex，长度小于4的话用0在前面补充
        :param data:
        :return:
        """
        data_len = hex(len(data) // 2)[2:]
        zero_pad = '0' * (4 - len(data_len))
        data_len = zero_pad + data_len
        return data_len

    @staticmethod
    def combine_c0(tx_power, pll_channel_id, work_mode):
        """
        初始化指令。软件在与天线建立网络连接后发送该指令，天线应答B0帧。
        :param tx_power: 天线功率级数，值为0~31，值越大表示功率越大，交易距离越远
        :param pll_channel_id: 信道号，值为0或1，代表不同的频率信道。相邻的两台天线设置成不同的值，可以防止距离较近的两台天线产生同频干扰影响交易。
        :param work_mode: 值为0标识表示正常模式，同一个标签最短20秒交易一次。 值为0x54(字母T的ASCII码)时，为测试模式，开启连续交易测试模式。值为0x45(字母E的ASCII码)时，表示不解密车辆信息，B4帧上传车辆信息密文
        :return:
        """
        seconds = hex(int(time.time()))[2:]
        data = ''.join(['c0', seconds, tx_power, pll_channel_id, work_mode])
        data_len = CommandSendSet.get_data_len(data)
        c0 = 'ffff' + data_len + data
        crc = CommonUtil.crc_jinyi(c0)
        c0 = c0 + crc
        return c0

    @staticmethod
    def combine_c1(obuid):
        """
        交易完成指令
        :param obuid:
        :return:
        """
        data = 'c1' + obuid
        data_len = CommandSendSet.get_data_len(data)
        c1 = 'ffff' + data_len + data
        crc = CommonUtil.crc_jinyi(c1)
        c1 = c1 + crc
        return c1

    @staticmethod
    def combine_c2(obuid):
        """
        忽略交易指令
        :param obuid:
        :return:
        """
        data = 'c2' + obuid
        data_len = CommandSendSet.get_data_len(data)
        c1 = 'ffff' + data_len + data
        crc = CommonUtil.crc_jinyi(c1)
        c1 = c1 + crc
        return c1

    @staticmethod
    def combine_c4(rsu_switch):
        """
        组合c4命令
        :param rsu_switch:  01：打开天线  00：关闭天线
        :return:
        """
        data = 'c4' + rsu_switch
        data_len = CommandSendSet.get_data_len(data)
        c4 = 'ffff' + data_len + data
        crc = CommonUtil.crc_jinyi(c4)
        c4 = c4 + crc
        return c4

    @staticmethod
    def combine_c6(obuid, consume_money, purchase_time, station_info, entry_time):
        """
        组合c6命令: 出口扣费指令
        :param obuid: OBU号
        :param consume_money: 扣款额，高位在前。单位为分
        :param purchase_time: 当前扣费时间。BCD编码格式，yyyyMMddHHmmss 例：20200412201745
        :param station_info: 过站信息，不需要可以填充0
        :param entry_time: 车辆入场时间。BCD编码格式，yyyyMMddHHmmss
        :return:
        """
        data = ''.join(['c6', obuid, consume_money, purchase_time, station_info, entry_time])
        data_len = CommandSendSet.get_data_len(data)
        c6 = 'ffff' + data_len + data
        crc = CommonUtil.crc_jinyi(c6)
        c6 = c6 + crc
        return c6

    @staticmethod
    def combine_ca():
        """
        组合ca命令  PSAM授权初始化
        :param rsu_switch:  01：打开天线  00：关闭天线
        :return:
        """
        data = 'ca'
        data_len = CommandSendSet.get_data_len(data)
        ca = 'ffff' + data_len + data
        crc = CommonUtil.crc_jinyi(ca)
        ca = ca + crc
        return ca

    @staticmethod
    def combine_cb(auth_mac):
        """
        组合ca命令  PSAM授权
        :param rsu_switch:  01：打开天线  00：关闭天线
        :return:
        """
        data = 'cb' + auth_mac
        data_len = CommandSendSet.get_data_len(data)
        cb = 'ffff' + data_len + data
        crc = CommonUtil.crc_jinyi(cb)
        cb = cb + crc
        return cb


if __name__ == '__main__':
    c0 = CommandSendSet.combine_c0(tx_power='0a', pll_channel_id='00', work_mode='00')
    print(c0)

    ca = CommandSendSet.combine_ca()
    print(ca)

    c1 = CommandSendSet.combine_c1(obuid='02f7d593')
    print(c1)

    c4 = CommandSendSet.combine_c4(rsu_switch='01')
    print(c4)
    c6 = CommandSendSet.combine_c6(obuid='02f7d593', consume_money='00000000', purchase_time='20201020170556',
                                   station_info='aa2900a1a2a3a4a5a6a7a8a1a2a3a4a5a6a7a8a1a2a3a4a5a6a7a8a1a2a3a4a5a6a7a8a1a2a3a4a5a6a7a8',
                                   entry_time='20201020170556')
    print(c6)
