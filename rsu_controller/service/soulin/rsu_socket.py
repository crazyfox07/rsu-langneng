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
from service.soulin.command_receive_set import CommandReceiveSet
from service.soulin.command_send_set import CommandSendSet
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
        msg_str = CommonUtil.transfer_recv_command(msg_bytes.hex())  # 字节转十六进制
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

    @func_set_timeout(CommonConf.ETC_CONF_DICT['recv_msg_max_wait_time'])
    def recv_msg_max_wait_time(self):
        # 接收数据
        msg_bytes_hex = self.socket_client.recv(1024).hex()
        msg_str = CommonUtil.transfer_recv_command(msg_bytes_hex)
        return msg_str

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
        result = dict(flag=False,
                      data=None,
                      error_msg=None)
        # 统计扣费期间b2的数量，有时会遇到b2->c1-b2->c1->b2->c1这样的无限循环
        count_b2 = 0
        # 设置超时时间
        while True:
            # 接收数据
            try:
                msg_bytes = self.recv_msg()
            except:
                logger.error('搜索obu超时')
                result['error_msg'] = '没有搜索到obu'
                return result
            # 指令转义
            msg_str = CommonUtil.transfer_recv_command(msg_bytes.hex()) # 字节转十六进制
            logger.info('接收数据： {}'.format(repr(msg_str)))
            # b2 电子标签信息帧
            if msg_str[6:8] == 'b2':
                if msg_str[8:16] == 'ffffffff':  # 'ffffffff' 表示心跳
                    logger.info('心跳')
                elif msg_str[68:72] == '2001':
                    info_b2 = self.command_recv_set.parse_b2(msg_str)  # 解析b2指令
                    # 过期日期
                    data_of_expire = self.command_recv_set.info_b2['DataOfExpire']
                    # 当前日期
                    data_of_now = CommonUtil.timestamp_format(int(time.time()), '%Y%m%d')
                    if data_of_now > data_of_expire:
                        result['error_msg'] = '过期日期：{}'.format(data_of_expire)
                        return result
                    # 电子标签mac地址
                    obuid = info_b2['OBUID']
                    # 获取c1指令
                    c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=self.rsu_conf['obu_div_factor'])
                    logger.info('b2后发送c1指令：%s' % (c1))
                    self.socket_client.send(bytes.fromhex(c1))
                    count_b2 += 1
                    if count_b2 > 3:
                        result['error_msg'] = '无法扣费，陷入b2->c1-b2->c1->b2->c1循环'
                        return result
                else:
                    result['error_msg'] = 'obu卡有问题，obu状态码： {}'.format(msg_str[68:72])
                    return result
            # b3 车辆信息帧
            elif msg_str[6:8] == 'b3':
                if msg_str[16: 18] == '00':  # obu信息帧状态执行码，取值00正常
                    self.command_recv_set.parse_b3(msg_str)  # 解析b3指令
                    # TODO 车牌号，车颜色 需要校验， 不匹配需要返回
                    plate_no = self.command_recv_set.info_b3['VehicleLicencePlateNumber']
                    try:
                        plate_no = CommonUtil.parse_plate_code(plate_no).replace('测A', '鲁L')
                    except:
                        logger.error(traceback.format_exc())
                        logger.error('车牌号解析错误：{}'.format(repr(plate_no)))
                    # 车牌颜色
                    obu_plate_color = str(
                        int(self.command_recv_set.info_b3['VehicleLicencePlateColor'], 16))  # obu车颜色
                    if (obu_body.plate_no != plate_no):
                        error_msg = '车牌号不匹配，监控获取的车牌号：%s,obu获取的车牌号：%s'.format(
                            obu_body.plate_no, plate_no)

                        result['error_msg'] = error_msg
                        return result
                    elif int(obu_body.plate_color_code) != int(obu_plate_color):
                        error_msg = "车牌号或车颜色不匹配： 监控获取的车牌号：%s, 车颜色：%s; obu获取的车牌号：%s,车颜色：%s" % (
                            obu_body.plate_no, obu_body.plate_color_code, plate_no, obu_plate_color)
                        logger.error(error_msg)
                        # todo 颜色不对，继续扣费
                    if obuid is None:  # 如果没有获取到obuid，继续
                        logger.error('obuid is none =====================+++++++++++++++++++')
                        continue
                    # 再次获取c1指令并发送
                    c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=self.rsu_conf['obu_div_factor'])
                    logger.info('b3后发送c1指令：%s' % (c1,))
                    self.socket_client.send(bytes.fromhex(c1))
                else:  # 状态执行码不正常，发送c2指令，终止交易
                    c2 = CommandSendSet.combine_c2(obuid, stop_type='01')
                    # logger.info('发送c2指令，终止交易:  %s' % (c2,))
                    self.socket_client.send(bytes.fromhex(c2))
                    result['error_msg'] = '终止交易'
                    return result
            # b4 速通卡信息帧
            elif msg_str[6:8] == 'b4':
                if msg_str[16: 18] == '00':  # 状态执行码，00说明后续速通卡信息合法有效
                    logger.info('接收b4指令： {}'.format(msg_str))
                    self.command_recv_set.parse_b4(msg_str)  # 解析b4指令
                    logger.info('b4解析后：{}'.format(json.dumps(self.command_recv_set.info_b4, ensure_ascii=False)))
                    # 获取并发送c6消费交易指令
                    if CommonConf.ETC_CONF_DICT['debug'] == 'true':
                        deduct_amount = CommonUtil.etcfee_to_hex(0.01)
                    else:
                        deduct_amount = CommonUtil.etcfee_to_hex(obu_body.deduct_amount)  # 扣款额，高字节在前
                    purchase_time = CommonUtil.timestamp_format(int(time.time()))
                    station = msg_str[132:212]  # 过站信息,40个字节
                    c6 = CommandSendSet.combine_c6(obuid, card_div_factor=self.rsu_conf['obu_div_factor'],
                                                   reserved='00000000',
                                                   deduct_amount=deduct_amount, purchase_time=purchase_time,
                                                   station=station)
                    # 针对红门轮训模式
                    if (not CommonConf.ETC_CONF_DICT['thirdApi']['etc_deduct_notify_url']) and (
                            datetime.datetime.now() - obu_body.create_time).seconds > CommonConf.ETC_CONF_DICT[
                        'hongmen_wait_time']:
                        error_msg = '时间超时，终止etc交易'
                        logger.info(error_msg)
                        result['error_msg'] = error_msg
                        return result
                    logger.info('b4后发送c6指令，消费交易，出口消费写过站: {}， 其中扣除费用{}'.format(c6, obu_body.deduct_amount))
                    self.socket_client.send(bytes.fromhex(c6))
                else:
                    result['error_msg'] = 'b4指令有问题'
                    return result
            # b5 交易信息帧，表示此次交易成功结束
            elif msg_str[6:8] == 'b5':
                if msg_str[16: 18] == '00':  # 状态执行码，00说明正常
                    self.command_recv_set.parse_b5(msg_str)  # 解析b5指令
                    #  获取并发送c1继续交易指令
                    c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=self.rsu_conf['obu_div_factor'])
                    logger.info('b5后发送c1指令：%s， 电子标签mac地址 obuid = %s' % (c1, obuid))
                    self.socket_client.send(bytes.fromhex(c1))
                    self.etc_charge_flag = True
                    result['flag'] = True
                    result['data'] = self.command_recv_set
                    return result
                else:
                    result['error_msg'] = 'b5指令有问题'
                    return result
            elif not msg_str:
                result['error_msg'] = '接收到的指令为空'
                return result
            elif not msg_str.startswith('ffff'):
                logger.info('忽略指令： {}'.format(msg_str))
            else:
                logger.error('未能解析的指令：%s' % (msg_str))

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
        # self.command_recv_set.print_obu_info()
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
        # 卡片发行信息
        issuer_info = self.command_recv_set.info_b4['IssuerInfo']
        # ETC 卡片类型（22:储值卡；23:记账卡）, 位于issuer_info的16,17位， 16进制形式，需要转为10进制
        card_type = str(int(issuer_info[16: 18], 16))
        # PSAM 卡编号
        psam_id = issuer_info[20: 40]
        #  card_sn 物理卡号
        card_sn = psam_id[4:]
        # TODO 待确认
        logger.info('ETC 卡片类型（22:储值卡；23:记账卡）: {}'.format(card_type))
        params = dict(algorithm_type="1",
                      # TODO 金额位数待确定
                      balance=CommonUtil.hex_to_etcfee(balance, unit='fen'),  # 交易后余额
                      # TODO 待确认
                      card_net_no=issuer_info[20:24],  # 网络编号
                      card_rnd=CommonUtil.random_str(8),  # 卡内随机数
                      card_serial_no=self.command_recv_set.info_b5['ICCPaySerial'],  # 卡内交易序号
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
                      trans_before_balance=CommonUtil.hex_to_etcfee(trans_before_balance, unit='fen'), # 交易前余额 1999918332 单位分
                      trans_order_no=body.trans_order_no,  # 交易订单号 "6711683258167489287"
                      trans_type=self.command_recv_set.info_b5['TransType'],  # 交易类型（06:传统；09:复合）
                      vehicle_type=str(int(self.command_recv_set.info_b3['VehicleClass']))  # 收费车型
                      )
        if params['trans_before_balance'] - params['deduct_amount'] != params['balance']:
            result['error_msg'] = '交易前余额 - 扣款 != 交易后余额'
            logger.error(str(params))
            return result
        # etc_deduct_info_dict = {"method": "etcPayUpload",
        #                         "params": params}
        # # 业务编码报文json格式
        # etc_deduct_info_json = json.dumps(etc_deduct_info_dict, ensure_ascii=False)
        # # 进行到此步骤，表示etc扣费成功，如果etc_deduct_notify_url不为空，通知抬杆
        # if CommonConf.ETC_CONF_DICT['thirdApi']['etc_deduct_notify_url']:
        #     payTime = CommonUtil.timeformat_convert(exit_time, format1='%Y%m%d%H%M%S', format2='%Y-%m-%d %H:%M:%S')
        #     res_etc_deduct_notify_flag = ThirdEtcApi.etc_deduct_notify(self.rsu_conf['park_code'], body.trans_order_no,
        #                                                            body.discount_amount, body.deduct_amount, payTime)
        # else:
        #     res_etc_deduct_notify_flag = True
        # if res_etc_deduct_notify_flag:
        #     # 接收到强哥返回值后，上传etc扣费数据
        #     upload_flag, upload_fail_count = ThirdEtcApi.etc_deduct_upload(etc_deduct_info_json)
        #     db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
        #                                               sqlite_database='etc_deduct.sqlite')
        #     # etc_deduct_info_json入库
        #     DBClient.add(db_session=db_session,
        #                  orm=ETCFeeDeductInfoOrm(id=CommonUtil.random_str(32).lower(),
        #                                          trans_order_no=body.trans_order_no,
        #                                          etc_info=etc_deduct_info_json,
        #                                          upload_flag=upload_flag,
        #                                          upload_fail_count=upload_fail_count))
        #     db_session.close()
        #     db_engine.dispose()

        # 清除收集到的b2，b3, b4, b5
        self.command_recv_set.clear_info_b2345()
        result['flag'] = True
        result['data'] = params
        result['exit_time'] = exit_time
        return result

    def close_socket(self):
        """
        关闭天线
        :return:
        """
        try:
            # 天线开关关闭
            self.rsu_on_or_off = StatusFlagConfig.RSU_OFF
            # 关闭天线指令
            c4 = CommandSendSet.combine_c4('00')
            logger.info('关闭天线指令：%s' % (c4))
            self.socket_client.send(bytes.fromhex(c4))
            # 关闭socket
            self.socket_client.shutdown(2)
            self.socket_client.close()
        except:
            logger.error(traceback.format_exc())


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
