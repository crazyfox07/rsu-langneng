#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:rsu_socket.py
@time:2020/12/30
"""
import datetime
import json
import socket
import time

from func_timeout import func_set_timeout

from common.config import StatusFlagConfig, CommonConf
from common.db_client import create_db_session, DBClient
from common.log import logger
from common.utils import CommonUtil
from model.db_orm import ETCRequestInfoOrm, ETCFeeDeductInfoOrm
from service.third_etc_api import ThirdEtcApi
from service.wanji.command_receive_set import CommandReceiveSet
from service.wanji.command_send_set import CommandSendSet


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
        self.init_rsu()

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
        # 创建一个客户端的socket对象
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接服务端
        self.socket_client.connect((self.rsu_conf['ip'], self.rsu_conf['port']))
        logger.info('=============================天线初始化=============================')
        # # 发送c0初始化指令
        c0 = CommandSendSet.combine_c0(lane_mode=self.rsu_conf['lane_mode'], bst_interval=self.rsu_conf['bst_interval'],
                                       tx_power=self.rsu_conf['tx_power'],
                                       pll_channel_id=self.rsu_conf['pll_channel_id'],
                                       trans_mode=self.rsu_conf['trans_mode'], flag_id=self.rsu_conf['flag_id'])
        logger.info('发送c0初始化指令： %s' % (c0,))
        self.socket_client.send(bytes.fromhex(c0))
        # 接收数据
        msg_bytes = self.socket_client.recv(1024)
        msg_str = msg_bytes.hex()  # 字节转十六进制
        logger.info('接收数据： {}'.format(repr(msg_str)))
        # 打开天线指令
        time.sleep(1)
        c4 = CommandSendSet.combine_c4('01').upper()
        # c4 = 'FFFF001000000002C4013F41'
        logger.info('发送c4打开天线指令： %s' % (c4,))
        self.socket_client.send(bytes.fromhex(c4))
        # 接收数据
        msg_str = self.socket_client.recv(1024).hex()
        print(json.dumps(self.command_recv_set.parse_b1(msg_str)))
        logger.info('接收数据： {}'.format(repr(msg_str)))

    @func_set_timeout(CommonConf.FUNC_TIME_OUT - 2)
    def recv_msg(self):
        # 接收数据
        msg_bytes = self.socket_client.recv(1024)
        return msg_bytes

    @func_set_timeout(CommonConf.ETC_CONF_DICT['recv_msg_max_wait_time'])
    def recv_msg_max_wait_time(self):
        # 接收数据
        msg_bytes_hex = self.socket_client.recv(1024).hex()
        msg_str = CommonUtil.transfer_recv_command(msg_bytes_hex)
        return msg_str

    def fee_deduction(self, obu_body: ETCRequestInfoOrm):
        """
        交易指令流程： b2 -> c1 -> b4 -> c6 -> b5 ->c1
        """
        logger.info('==========================================开始扣费==========================================')
        logger.info('订单号：{}， 车牌号：{}， 车牌颜色：{}'.format(
            obu_body.trans_order_no, obu_body.plate_no, obu_body.plate_color_code))
        # self.etc_charge_flag=True表示交易成功，self.etc_charge_flag=False表示交易失败
        self.etc_charge_flag = False
        result = dict(flag=False,
                      data=None,
                      error_msg=None)
        # 设置超时时间
        while True:
            # 接收数据
            try:
                msg_str = self.recv_msg().hex()
            except:
                logger.error('搜索obu超时')
                result['error_msg'] = '没有搜索到obu'
                return result
            logger.info('接收数据： {}'.format(repr(msg_str)))
            # b1 心跳
            if msg_str[16: 18] == 'b1':
                # logger.info('接收b1心跳数据：{}'.format(msg_str))
                if msg_str[18: 20] == '00':
                    self.rsu_heartbeat_time = datetime.datetime.now()
                else:
                    logger.error('天线心跳出现问题')
                    result['error_msg'] = '天线心跳出现问题'
                    return result
            # 车载单元信息帧
            elif msg_str[16: 18] == 'b2':
                if msg_str[26: 28] == '00':  # 执行状态代码，取值为“00H”时有后续数据
                    info_b2 = self.command_recv_set.parse_b2(msg_str)  # 解析b2指令
                    obuid = info_b2['OBUID']
                    # todo 待定
                    obu_div_factor = info_b2['IssuerIdentifier']
                    # 发送c1指令
                    c1 = CommandSendSet.combine_c1(obuid, obu_div_factor)
                    logger.info('发送c1指令：{}'.format(c1))
                    self.socket_client.send(bytes.fromhex(c1))
                    continue
                else:
                    logger.error('车载单元信息帧出错')
                    result['error_msg'] = '车载单元信息帧出错'
            # 用户信息帧
            elif msg_str[16: 18] == 'b4':
                if msg_str[26: 28] == '00':  # 执行状态代码，取值为“00H”时有后续数据
                    info_b4 = self.command_recv_set.parse_b4(msg_str)  # 解析b4指令
                    consume_money = CommonUtil.etcfee_to_hex(obu_body.deduct_amount)
                    purchase_time = CommonUtil.timestamp_format(int(time.time()))
                    station = info_b4['LastStation']
                    plate_no = CommonUtil.parse_plate_code(info_b4['VehicleInfo'][:24])
                    # 车牌颜色
                    obu_plate_color = str(int(self.command_recv_set.info_b4['VehicleInfo'][24: 26], 16))  # obu车颜色
                    if (obu_body.plate_no != plate_no) or (int(obu_body.plate_color_code) != int(obu_plate_color)):
                        error_msg = "车牌号或车颜色不匹配： 监控获取的车牌号：%s, 车颜色：%s; obu获取的车牌号：%s,车颜色：%s" % (
                            obu_body.plate_no, obu_body.plate_color_code, plate_no, obu_plate_color)
                        logger.error(error_msg)
                        result['error_msg'] = error_msg
                        return result
                    # 发送c6消费交易指令
                    c6 = CommandSendSet.combine_c6(obuid, obu_div_factor, consume_money, purchase_time, station)
                    logger.info('发送c6指令：{}'.format(c6))
                    self.socket_client.send(bytes.fromhex(c6))
                    continue
                else:
                    logger.error('用户信息帧出错')
                    result['error_msg'] = '用户信息帧出错'
            # 交易信息帧
            elif msg_str[16: 18] == 'b5':
                b5 = self.command_recv_set.parse_b5(msg_str)
                logger.info(json.dumps(b5, ensure_ascii=False))
                if msg_str[26: 28] == '00':  # 执行状态代码，取值为“00H”时有后续数据
                    logger.info('发送c1指令：{}'.format(c1))
                    self.socket_client.send(bytes.fromhex(c1))
                    self.etc_charge_flag = True
                    result['flag'] = True
                    result['data'] = self.command_recv_set
                    return result
                else:
                    logger.error('交易信息帧出错')
                    result['error_msg'] = '交易信息帧出错'
            else:
                logger.error('未能解析的指令')

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
        # TODO 待待删打印信息
        # self.print_trans_info()
        #  判断card_net和card_sn 物理卡号是否存在于黑名单中
        card_sn_in_blacklist_flag, error_msg = self.card_sn_in_blacklist()
        # 物理卡号存在于黑名单中直接返回
        if card_sn_in_blacklist_flag:
            result['error_msg'] = error_msg
            return result
        # 入场时间戳格式化 yyyyMMddHHmmss
        entrance_time = CommonUtil.timestamp_format(body.entrance_time, format='%Y%m%d%H%M%S')
        # 交易时间格式化（yyyyMMddHHmmss）
        # exit_time = CommonUtil.timestamp_format(body.exit_time, format='%Y%m%d%H%M%S')
        exit_time = self.command_recv_set.info_b5['TransTime']
        exit_time_stamp = CommonUtil.str_to_timestamp(timestr=exit_time, format='%Y%m%d%H%M%S')
        # 计算停车时长
        park_record_time = CommonUtil.time_difference(body.entrance_time, exit_time_stamp)
        # 交易后余额
        balance = self.command_recv_set.info_b5['CardBalance']
        # 交易前余额 1999918332 单位分
        trans_before_balance = self.command_recv_set.info_b4['CardRestMoney']
        if CommonConf.ETC_CONF_DICT['debug'] == 'true':
            deduct_amount = 0.01
        else:
            deduct_amount = body.deduct_amount

        card_net_no = self.command_recv_set.info_b4['IssuerInfo'][20: 24]  # 网络编号
        # ETC 卡片类型 16 储值卡  17 记账卡，转换成十进制分别对应22,23
        card_type = str(int(self.command_recv_set.info_b4['IssuerInfo'][16: 18], 16))
        # PSAM 卡编号 10字节
        try:
            psam_id = self.command_recv_set.info_b4['IssuerInfo'][20: 40]
        except:
            print(self.command_recv_set.info_b4)
        #  card_sn 物理卡号 8字节
        card_sn = psam_id[4:]
        # TODO 待确认
        logger.info('ETC 卡片类型（22:储值卡；23:记账卡）: {}'.format(card_type))
        params = dict(algorithm_type="1",
                      # TODO 金额位数待确定
                      balance=CommonUtil.hex_to_etcfee(balance, unit='fen'),  # 交易后余额
                      # TODO 待确认
                      card_net_no=card_net_no,  # 网络编号
                      card_rnd=CommonUtil.random_str(8),  # 卡内随机数
                      card_serial_no=self.command_recv_set.info_b5['ICCPayserial'],  # 卡内交易序号
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
                      issuer_identifier=self.command_recv_set.info_b2['IssuerIdentifier'].upper(),  # 发行商代码
                      obu_id=self.command_recv_set.info_b2['OBUID'].upper(),  # OBU 序号编码
                      park_code=self.rsu_conf['park_code'],  # 车场编号
                      park_record_time=park_record_time,  # 停车时长,时间精确到秒， 6小时50分钟
                      plate_color_code=body.plate_color_code,  # 车牌颜色编码 0:蓝色、1:黄色、2:黑色、3:白色、4:渐变绿色、5:黄绿双拼、6:绿色、7:蓝白渐变
                      plate_no=body.plate_no,  # 车牌号码 "皖LX4652",
                      plate_type_code=body.plate_type_code,  # 车辆类型编码 0:小车 1:大车 2:超大车
                      psam_id=psam_id,  # PSAM 卡编号 "37010101000000295460"
                      psam_serial_no=self.command_recv_set.info_b5['PSAMTransSerial'],  # PSAM 流水号 "00005BA2",
                      receivable_total_amount=CommonUtil.yuan_to_fen(body.receivable_total_amount),  # 应收金额
                      serial_number=self.command_recv_set.info_b2['SerialNumber'],  # 合同序列号"340119126C6AFEDE"
                      tac=self.command_recv_set.info_b5['TAC'],  # 交易认证码
                      terminal_id=self.command_recv_set.info_b5['PSAMNo'],  # 终端编号
                      trans_before_balance=CommonUtil.hex_to_etcfee(trans_before_balance, unit='fen'),  # 交易前余额 1999918332 单位分
                      trans_order_no=body.trans_order_no,  # 交易订单号 "6711683258167489287"
                      trans_type='09',  # 交易类型（06:传统；09:复合）
                      vehicle_type=str(int(self.command_recv_set.info_b4['VehicleInfo'][26: 28]))  # 收费车型
                      )
        etc_deduct_info_dict = {"method": "etcPayUpload",
                                "params": params}
        # 业务编码报文json格式
        etc_deduct_info_json = json.dumps(etc_deduct_info_dict, ensure_ascii=False)
        # 进行到此步骤，表示etc扣费成功，如果etc_deduct_notify_url不为空，通知抬杆
        if CommonConf.ETC_CONF_DICT['thirdApi']['etc_deduct_notify_url']:
            payTime = CommonUtil.timeformat_convert(exit_time, format1='%Y%m%d%H%M%S', format2='%Y-%m-%d %H:%M:%S')
            res_etc_deduct_notify_flag = ThirdEtcApi.etc_deduct_notify(self.rsu_conf['park_code'], body.trans_order_no,
                                                                       body.discount_amount, body.deduct_amount,
                                                                       payTime)
        else:
            res_etc_deduct_notify_flag = True
        if res_etc_deduct_notify_flag:
            # 接收到强哥返回值后，上传etc扣费数据
            upload_flag, upload_fail_count = ThirdEtcApi.etc_deduct_upload(etc_deduct_info_json)
            db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                                      sqlite_database='etc_deduct.sqlite')
            # etc_deduct_info_json入库
            DBClient.add(db_session=db_session,
                         orm=ETCFeeDeductInfoOrm(id=CommonUtil.random_str(32).lower(),
                                                 trans_order_no=body.trans_order_no,
                                                 etc_info=etc_deduct_info_json,
                                                 upload_flag=upload_flag,
                                                 upload_fail_count=upload_fail_count))
            db_session.close()
            db_engine.dispose()

        # 清除收集到的b2，b3, b4, b5
        self.command_recv_set.clear_info_b12345()
        result['flag'] = True
        result['data'] = params
        return result

    def card_sn_in_blacklist(self):
        """
        黑名单查询
        :return:
        """
        issuer_info = self.command_recv_set.info_b4['IssuerInfo']
        card_net = str(issuer_info[20: 24])
        # 平台参数下载-发行方黑名单接口：针对某些card_net不进行etc
        if ThirdEtcApi.exists_in_fxf_blacklist(card_net):
            return True, 'card_net: {} in blacklist'.format(card_net)
        card_sn = issuer_info[24: 40]
        issuer_identifier = self.command_recv_set.info_b2['IssuerIdentifier']
        card_sn_in_blacklist_flag = ThirdEtcApi.exists_in_blacklist(
            issuer_identifier=issuer_identifier, card_net=card_net, card_id=card_sn)
        error_msg = None
        if card_sn_in_blacklist_flag:
            error_msg = 'card_id:%s in blacklist' % card_sn
            logger.error(error_msg)
        return card_sn_in_blacklist_flag, error_msg

    def print_trans_info(self):
        logger.info('---------------------b2-----------------------')
        logger.info(json.dumps(self.command_recv_set.info_b2, ensure_ascii=False))
        logger.info('---------------------b4-----------------------')
        logger.info(json.dumps(self.command_recv_set.info_b4, ensure_ascii=False))
        logger.info('---------------------b5-----------------------')
        logger.info(json.dumps(self.command_recv_set.info_b5, ensure_ascii=False))


if __name__ == '__main__':
    rsu_socket = RsuSocket('002')
    obu_body = ETCRequestInfoOrm(id='123456', lane_num='002', trans_order_no='123456', park_code='371187',
                                 plate_no='鲁L71R86', plate_color_code='0', plate_type_code='0',
                                 entrance_time=int(time.time())-100, park_record_time=100, exit_time=int(time.time()),
                                 deduct_amount=0.00, receivable_total_amount=0.00, discount_amount=0)
    result = rsu_socket.fee_deduction(obu_body)
    result2 = rsu_socket.handle_data(obu_body)
    logger.info(json.dumps(result2, ensure_ascii=False))
    rsu_socket.print_trans_info()
