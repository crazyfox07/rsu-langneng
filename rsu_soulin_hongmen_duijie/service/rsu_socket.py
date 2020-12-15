# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: rsu_socket.py
@time: 2020/9/17 11:50
"""
import json
import time
import datetime
import socket
import traceback

from func_timeout import func_set_timeout

from common.config import CommonConf, StatusFlagConfig
from common.db_client import DBClient, create_db_session
from common.log import logger
from common.utils import CommonUtil
from model.db_orm import ETCFeeDeductInfoOrm, ETCRequestInfoOrm
from model.obu_model import OBUModel
from service.command_receive_set import CommandReceiveSet
from service.command_send_set import CommandSendSet
from service.third_etc_api import ThirdEtcApi


class RsuSocket(object):
    """
    搜林天线socket
    """

    def __init__(self, lane_num):
        # 车道号
        self.lane_num = lane_num
        # 天线状态, 默认有故障
        self.rsu_status = StatusFlagConfig.RSU_FAILURE
        # 天线开关状态
        self.rsu_on_or_off = StatusFlagConfig.RSU_ON
        # 天线心跳的最新时间
        self.rsu_heartbeat_time = datetime.datetime.now()
        # 检测到obu的最新时间
        self.detect_obu_time_latest = time.time()
        # 根据车道号获取天线配置
        self.rsu_conf = self.get_rsu_conf_by_lane_num(lane_num)
        # socket重建次数
        self.recreate_socket_count = 0
        # 创建命令收集对象，用于后期解析天线发送过来的命令
        self.command_recv_set = CommandReceiveSet()
        # 初始化天线
        # self.init_rsu()

    def get_rsu_conf_by_lane_num(self, lane_num):
        """
        通过车道号获取对应天线配置
        :return:
        """
        rsu_conf_list = CommonConf.ETC_CONF_DICT['etc']
        rsu_conf = next(filter(lambda item: item['lane_num'] == lane_num, rsu_conf_list))
        return rsu_conf

    def init_rsu(self):
        """
        初始化rsu, 初始化耗时大约1s
        :return:
        """
        # 天线开关开启
        self.rsu_on_or_off = StatusFlagConfig.RSU_ON
        # if 'socket_client' in dir(self):
        #     del self.socket_client
        # 创建一个客户端的socket对象
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接服务端
        self.socket_client.connect((self.rsu_conf['ip'], self.rsu_conf['port']))
        logger.info('=============================天线初始化=============================')
        # 设置连接超时
        # self.socket_client.settimeout(CommonConf.ETC_CONF_DICT['socket_connect_time_out'])
        # 天线功率， 十进制转16进制
        tx_power = hex(self.rsu_conf['tx_power'])[2:]
        if len(tx_power) == 1:
            tx_power = '0' + tx_power
        # 发送c0初始化指令，以二进制的形式发送数据，所以需要进行编码
        c0 = CommandSendSet.combine_c0(lane_mode=self.rsu_conf['lane_mode'], wait_time=self.rsu_conf['wait_time'],
                                       tx_power=tx_power,
                                       pll_channel_id=self.rsu_conf['pll_channel_id'],
                                       trans_mode=self.rsu_conf['trans_mode']).strip()
        logger.info('发送c0初始化指令： %s' % (c0,))
        self.socket_client.send(bytes.fromhex(c0))

        # 接收数据
        msg_bytes = self.socket_client.recv(1024)
        msg_str = msg_bytes.hex()  # 字节转十六进制
        logger.info('接收数据： {}'.format(repr(msg_str)))
        # b0 天线设备状态信息帧
        if msg_str[6: 8] == 'b0':
            self.command_recv_set.parse_b0(msg_str)  # 解析b0指令
            if self.command_recv_set.info_b0['RSUStatus'] == '00':
                self.rsu_status = StatusFlagConfig.RSU_NORMAL
                self.rsu_heartbeat_time = datetime.datetime.now()
            else:
                self.rsu_status = StatusFlagConfig.RSU_FAILURE
        elif msg_str == '' and self.recreate_socket_count < 2:  # 可能由于上次没有正常关闭，导致mst_st为空
            self.recreate_socket_count += 1
            self.close_socket()
            logger.info('==============再试一次初始化天线==============')
            #  再试一次初始化天线
            self.init_rsu()
        else:
            self.recreate_socket_count = 0

    @func_set_timeout(CommonConf.FUNC_TIME_OUT - 2)
    def recv_msg(self):
        # 接收数据
        msg_bytes = self.socket_client.recv(1024)
        return msg_bytes

    @func_set_timeout(130)
    def recv_msg_max_wait_time(self):
        # 接收数据
        msg_bytes = self.socket_client.recv(1024).hex().replace('fe01', 'ff').replace('fe00', 'fe')
        return msg_bytes

    def fee_deduction(self, obu_body: ETCRequestInfoOrm):
        """
        etc扣费, 正常扣费指令流程, 耗时大约700ms  c0->b0->b2->c1->b3->c1->b4->c6->b5，其中
        c0: 发送初始化指令  --> init_rsu()中已经初始化
        b0: 接收设备状态信息帧  --> nit_rsu()中已经初始化
        b2: 接收电子标签信息帧
        c1: 发送继续交易指令
        b3: 接收设备车辆信息帧
        c1: 发送继续交易指令
        b4: 接收速通卡信息帧
        c6: 发送消费交易指令，出口消费写过站
        b5: 接收交易信息帧，表示此次交易成功结束
        :return:
        """
        current_time = time.time()
        logger.info('==========================================开始扣费==========================================')
        logger.info('订单号：{}， 车牌号：{}， 车牌颜色：{}'.format(
            obu_body.trans_order_no, obu_body.plate_no, obu_body.plate_color_code))
        # self.etc_charge_flag=True表示交易成功，self.etc_charge_flag=False表示交易失败
        self.etc_charge_flag = False
        obuid = None
        result = dict(flag=True,
                      data=None,
                      error_msg=None)
        return result

    def handle_data(self, body: ETCRequestInfoOrm):
        """
        处理self.command_recv_set，也就是收到的天线的信息
        :param body: 接收到的数据
        :return:
        """
        # 结果存储
        result = dict(flag=False,
                      data=None,
                      error_msg=None)
        deduct_amount = body.deduct_amount
        # 入场时间戳格式化 yyyyMMddHHmmss
        entrance_time = CommonUtil.timestamp_format(body.entrance_time, format='%Y%m%d%H%M%S')
        # 交易时间格式化（yyyyMMddHHmmss）
        # exit_time = CommonUtil.timestamp_format(body.exit_time, format='%Y%m%d%H%M%S')
        exit_time = CommonUtil.timestamp_format(body.exit_time, format='%Y%m%d%H%M%S')
        exit_time_stamp = CommonUtil.str_to_timestamp(timestr=exit_time, format='%Y%m%d%H%M%S')
        # 计算停车时长
        park_record_time = CommonUtil.time_difference(body.entrance_time, exit_time_stamp)
        # 交易后余额
        balance = '123'
        # 交易前余额 1999918332 单位分
        trans_before_balance = '123'
        # 卡片发行信息
        issuer_info = '0000000000000000000000000000000000000000000000000'
        # ETC 卡片类型（22:储值卡；23:记账卡）, 位于issuer_info的16,17位， 16进制形式，需要转为10进制
        card_type = '23'
        # PSAM 卡编号
        psam_id = '000000000000000'
        #  card_sn 物理卡号
        card_sn = '0000000000000509'
        # TODO 待确认
        logger.info('ETC 卡片类型（22:储值卡；23:记账卡）: {}'.format(card_type))
        params = dict(algorithm_type="1",
                      # TODO 金额位数待确定
                      balance=CommonUtil.hex_to_etcfee(balance, unit='fen'),  # 交易后余额
                      # TODO 待确认
                      card_net_no=issuer_info[20:24],  # 网络编号
                      card_rnd=CommonUtil.random_str(8),  # 卡内随机数
                      card_serial_no='0129',  # 卡内交易序号
                      card_sn=card_sn,
                      # self.command_recv_set.info_b4['CardID'],  # "1030230218354952",ETC 支付时与卡物理号一致；非 ETC 时上传车牌号
                      card_type=card_type,  # "23",  # ETC 卡片类型（22:储值卡；23:记账卡）
                      charging_type="0",  # 扣费方式(0:天线 1:刷卡器)
                      deduct_amount=CommonUtil.yuan_to_fen(deduct_amount),  # 扣款金额
                      device_no=self.rsu_conf['device_no'],  # 设备号
                      device_type=self.rsu_conf['device_type'],  # 设备类型（0:天线；1:刷卡器；9:其它）
                      discount_amount=CommonUtil.yuan_to_fen(body.discount_amount),  # 折扣金额
                      entrance_time=entrance_time,  # 入场时间 yyyyMMddHHmmss
                      exit_time=exit_time,  # 交易时间（yyyyMMddHHmmss）
                      issuer_identifier='B9E3B6AB44010001',  # 发行商代码
                      obu_id='02F7D593',  # OBU 序号编码
                      park_code=self.rsu_conf['park_code'],  # 车场编号
                      park_record_time=park_record_time,  # 停车时长,时间精确到秒， 6小时50分钟
                      plate_color_code=body.plate_color_code,  # 车牌颜色编码 0:蓝色、1:黄色、2:黑色、3:白色、4:渐变绿色、5:黄绿双拼、6:绿色、7:蓝白渐变
                      plate_no=body.plate_no,  # 车牌号码 "皖LX4652",
                      plate_type_code=body.plate_type_code,  # 车辆类型编码 0:小车 1:大车 2:超大车
                      psam_id=psam_id,  # PSAM 卡编号 "37010101000000295460"
                      psam_serial_no='00000129',  # PSAM 流水号 "00005BA2",
                      receivable_total_amount=CommonUtil.yuan_to_fen(body.receivable_total_amount),  # 应收金额
                      serial_number='86030002200479e1',  # 合同序列号"340119126C6AFEDE"
                      tac=CommonUtil.random_str(8),  # 交易认证码
                      terminal_id='000000000509',  # 终端编号
                      trans_before_balance=CommonUtil.hex_to_etcfee(trans_before_balance, unit='fen'), # 交易前余额 1999918332 单位分
                      trans_order_no=body.trans_order_no,  # 交易订单号 "6711683258167489287"
                      trans_type='09',  # 交易类型（06:传统；09:复合）
                      vehicle_type='0'  # 收费车型
                      )
        result['flag'] = True
        result['data'] = params

        return result


if __name__ == '__main__':
    obu_model = OBUModel(
        lane_num="002",
        trans_order_no="1818620411622008760",
        park_code="371165",
        plate_no="鲁L12345",
        plate_color_code="0",
        plate_type_code="0",
        entrance_time=1600054273,
        park_record_time=100,
        exit_time=1600054373,
        deduct_amount=0.00,
        receivable_total_amount=0.00,
        discount_amount=0
    )
    try:
        time1 = time.time()
        rsusocket = RsuSocket('002')
        time2 = time.time()
        print('socket初始化用时： {}'.format(time2 - time1))
        rsusocket.fee_deduction(obu_model)
        time3 = time.time()
        print('扣费用时： {}'.format(time3 - time2))
        rsusocket.fee_deduction(obu_model)
        time4 = time.time()
        print('扣费用时2： {}'.format(time4 - time3))
    finally:
        print('================================================')
        rsusocket.close_socket()
