#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:command_send_set.py
@time:2020/12/30
"""
import time

from common.utils import CommonUtil


class CommandSendSet(object):
    stx = 'ffff'  # 帧开始标志
    ver = '00'  # 协议版本号
    seq = '00'  # 帧序列号

    @staticmethod
    def get_seq():
        seq_num = int(CommandSendSet.seq[0]) + 1
        if seq_num >= 10:
            seq_num = 1
        CommandSendSet.seq = str(seq_num) + '0'
        return CommandSendSet.seq

    @staticmethod
    def compute_len_data(data):
        len_data = len(data) // 2
        len_data = '0000' + '0' * (4 - len(hex(len_data)[2:])) + hex(len_data)[2:]
        return len_data

    @staticmethod
    def compute_crc(seq, len_data, data):
        value_verify = ''.join([CommandSendSet.stx, CommandSendSet.ver, seq, len_data, data])
        crc = CommonUtil.crc_jinyi(value_verify)
        return crc

    @staticmethod
    def combine_common_command(data):
        len_data = CommandSendSet.compute_len_data(data)
        seq = CommandSendSet.get_seq()
        crc = CommandSendSet.compute_crc(seq, len_data, data)
        command = ''.join([CommandSendSet.stx, CommandSendSet.ver, seq, len_data, data, crc])
        return command

    @staticmethod
    def combine_c0(lane_mode='13', bst_interval=10, tx_power=10, pll_channel_id='01', trans_mode='01', flag_id='371102'):
        """
        初始化指令c0指令
        """
        cmd_type = 'c0'
        seconds = hex(int(time.time()))[2:]
        data_time = CommonUtil.timestamp_format(int(time.time()))
        bst_interval = '0' + hex(bst_interval)[2:] if len(hex(bst_interval)[2:]) == 1 else hex(bst_interval)[2:] # 路测单元自动发送bst的间隔，单位ms，默认10ms
        tx_power = '0' + hex(tx_power)[2:] if len(hex(tx_power)[2:]) == 1 else hex(tx_power)[2:]  # 天线功率
        reserved = '0000'
        data = ''.join([cmd_type, seconds, data_time, lane_mode, bst_interval, tx_power, pll_channel_id, trans_mode,
                        flag_id, reserved])
        command = CommandSendSet.combine_common_command(data)
        return command

    @staticmethod
    def combine_c1(obu_id, obu_div_factor):
        """
        继续交易指令c1指令
        """
        cmd_type = 'c1'
        data = ''.join([cmd_type, obu_id, obu_div_factor])
        command = CommandSendSet.combine_common_command(data)
        return command

    @staticmethod
    def combine_c2(obu_id, stop_type):
        """
        停止交易指令c2指令
        :param stop_type: 01H 结束交易，重新搜索车载单元  02H 重新发送当前帧
        """
        cmd_type = 'c2'
        unix_time = hex(int(time.time()))[2:]
        data = ''.join([cmd_type, obu_id, stop_type, unix_time])
        command = CommandSendSet.combine_common_command(data)
        return command

    @staticmethod
    def combine_c4(control_type):
        """
        开关 路侧单元 指令 c4
        :param control_type: 00H：关闭 路侧单元 01H：打开 路侧单元 ；其他值保留
        """
        cmd_type = 'c4'
        data = ''.join([cmd_type, control_type])
        command = CommandSendSet.combine_common_command(data)
        return command

    @staticmethod
    def combine_c6(obu_id, obu_div_factor, consume_money, purchase_time, station):
        """
        消费交易指令c6 本 指令对路侧单元发送过来的 B4帧有效。
        :param consume_money: 本次 扣款 /计费金额（ 16进制 高字节在前，单位分）
        """
        cmd_type = 'c6'
        data = ''.join([cmd_type, obu_id, obu_div_factor, consume_money, purchase_time, station])
        command = CommandSendSet.combine_common_command(data)
        return command

    @staticmethod
    def combine_c8(obu_id, epserial):
        """
        重取 TAC指令  本指令使用场景：获取 TAC码信息 本指令对 B2、 B4帧有效 。
        :param consume_money: 本次 扣款 /计费金额（ 16进制 高字节在前，单位分）
        """
        cmd_type = 'c8'
        data = ''.join([cmd_type, obu_id, epserial])
        command = CommandSendSet.combine_common_command(data)
        return command



if __name__ == '__main__':
    [CommandSendSet.combine_c1('6a81354f', '0000000000000001') for _ in range(20)]