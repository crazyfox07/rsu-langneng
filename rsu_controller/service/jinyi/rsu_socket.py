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
from service.jinyi.command_receive_set import CommandReceiveSet
from service.jinyi.command_send_set import CommandSendSet
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
        t1 = time.time()
        logger.info('=============================天线初始化=============================')
        # 设置连接超时
        # self.socket_client.settimeout(CommonConf.ETC_CONF_DICT['socket_connect_time_out'])
        # 天线功率， 十进制转16进制
        tx_power = hex(self.rsu_conf['tx_power'])[2:]
        if len(tx_power) == 1:
            tx_power = '0' + tx_power

        # 创建一个客户端的socket对象
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # # 连接服务端
        self.socket_client.connect((self.rsu_conf['ip'], self.rsu_conf['port']))
        # 授权初始化
        ca = CommandSendSet.combine_ca()
        logger.info('授权初始化ca: {}'.format(ca))
        self.socket_client.send(bytes.fromhex(ca))
        ba = self.socket_client.recv(1024).hex()
        logger.info('接收授权初始化数据ba：{}'.format(ba))
        self.command_recv_set.parse_ba(ba)
        logger.info(self.command_recv_set.info_ba)
        # 授权
        # cb = CommandSendSet.combine_cb()
        # logger.info('授权初始化cb: {}'.format(cb))
        # self.socket_client.send(bytes.fromhex(cb))
        # msg_str = self.socket_client.recv(1024).hex()
        # logger.info('接收授权数据bb：{}'.format(msg_str))
        # 发送c0初始化指令，以二进制的形式发送数据，所以需要进行编码
        c0 = CommandSendSet.combine_c0(tx_power=tx_power, pll_channel_id=self.rsu_conf['pll_channel_id'],
                                       work_mode=self.rsu_conf['work_mode']).strip()
        logger.info('发送c0初始化指令： %s' % (c0,))
        self.socket_client.send(bytes.fromhex(c0))
        b0 = self.socket_client.recv(1024).hex()
        logger.info('接收初始化数据：{}'.format(b0))
        self.command_recv_set.parse_b0(b0)
        if b0[10: 12] == '00':
            self.rsu_status = StatusFlagConfig.RSU_NORMAL
        else:
            self.rsu_status = StatusFlagConfig.RSU_FAILURE
        t2 = time.time()
        logger.info('初始化用时： {}s'.format(t2 - t1))
        # 打开天线指令
        c4 = CommandSendSet.combine_c4('01')
        logger.info('发送c4打开天线指令： %s' % (c4,))
        self.socket_client.send(bytes.fromhex(c4))
        # self.socket_client.recv(1024)
        t3 = time.time()
        logger.info('打开天线用时： {}s'.format(t3 - t1))

    @func_set_timeout(CommonConf.FUNC_TIME_OUT - 2)
    def recv_msg(self):
        # 接收数据
        msg_bytes = self.socket_client.recv(1024)
        return msg_bytes

    @func_set_timeout(CommonConf.ETC_CONF_DICT['recv_msg_max_wait_time'])
    def recv_msg_max_wait_time(self):
        # 接收数据
        msg_bytes = self.socket_client.recv(1024).hex()
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
        logger.info('最新obu检查时间差：{}'.format(current_time - self.detect_obu_time_latest))
        # self.etc_charge_flag=True表示交易成功，self.etc_charge_flag=False表示交易失败
        self.etc_charge_flag = False
        obuid = None
        result = dict(flag=False,
                      data=None,
                      error_msg="error")

        while True:
            # 接收数据
            try:
                msg_bytes = self.recv_msg()
            except:
                logger.error('搜索obu超时')
                result['error_msg'] = '没有搜索到obu'
                return result
            # 指令转义
            msg_str = msg_bytes.hex()  # 字节转十六进制
            if msg_str[8:10] == 'b2':
                logger.info('接收b2心跳数据：{}'.format(msg_str))
                if msg_str[10:12] == '00':
                    self.rsu_heartbeat_time = datetime.datetime.now()
                else:
                    logger.error('天线心跳出现问题')
                    return result

            elif msg_str[8:10] == 'b4':
                info_b4 = self.command_recv_set.parse_b4(b4=msg_str)
                logger.info('接收b4: {}'.format(info_b4))
                obuid = info_b4['ObuID']
                # TODO 测试卡，正式环境要检测obu_status
                obu_status = info_b4['OBUStatus']
                # if obu_status == '01':
                #     result['error_msg'] = 'obu非法拆卸！！！'
                #     return result
                black_list_status = info_b4['BlackListStatus']
                if black_list_status == '01':
                    result['error_msg'] = '属于黑名单车辆！！!'
                    return result
                # 当前日期
                data_of_now = CommonUtil.timestamp_format(int(time.time()), '%Y%m%d')
                if data_of_now > info_b4['DataOfExpire']:
                    result['error_msg'] = '过期日期：{}'.format(info_b4['DataOfExpire'])
                    return result

                plate_no = info_b4['VehicleLicencePlateNumber']
                try:
                    plate_no = CommonUtil.parse_plate_code(plate_no).replace('测A', '鲁L')
                except:
                    logger.error(traceback.format_exc())
                    result['error_msg'] = '车牌号解析错误：{}'.format(repr(plate_no))
                    return result

                plate_color = str(int(info_b4['VehicleLicencePlateColor'], 16))
                # if (plate_no != obu_body.plate_no) or (plate_color != obu_body.plate_color_code):
                if (plate_no != obu_body.plate_no):
                    error_msg = '车牌号不匹配，监控获取的车牌号：%s,obu获取的车牌号：%s'.format(
                        obu_body.plate_no, plate_no)
                    result['error_msg'] = error_msg
                    return result
                elif plate_color != obu_body.plate_color_code:
                    error_msg = "车牌号或车颜色不匹配： 监控获取的车牌号：%s, 车颜色：%s; obu获取的车牌号：%s,车颜色：%s" % (
                        obu_body.plate_no, obu_body.plate_color_code, plate_no, plate_color)
                    logger.error(error_msg)
                    # todo 颜色不对，继续扣费

                consume_money = CommonUtil.etcfee_to_hex(obu_body.deduct_amount)  # 扣费金额
                purchase_time = CommonUtil.timestamp_format(int(time.time()), format='%Y%m%d%H%M%S')
                station_info = info_b4['StationInfo']
                entry_time = CommonUtil.timestamp_format(int(time.time()) - 100, format='%Y%m%d%H%M%S')
                c6 = CommandSendSet.combine_c6(obuid=obuid, consume_money=consume_money,
                                               purchase_time=purchase_time,
                                               station_info=station_info, entry_time=entry_time)
                # 针对红门轮训模式
                if (not CommonConf.ETC_CONF_DICT['thirdApi']['etc_deduct_notify_url']) and (
                        datetime.datetime.now() - obu_body.create_time).seconds > CommonConf.ETC_CONF_DICT[
                    'hongmen_wait_time']:
                    error_msg = '时间超时，终止etc交易'
                    logger.info(error_msg)
                    result['error_msg'] = error_msg
                    return result
                logger.info('b4后发送c6指令：{}'.format(c6))
                self.socket_client.send(bytes.fromhex(c6))
            elif msg_str[8:10] == 'b5':
                self.command_recv_set.parse_b5(b5=msg_str)
                logger.info('c6后接收b5指令：{}'.format(msg_str))
                if self.command_recv_set.info_b5['ErrorCode'] == '01':
                    logger.error('读取obu卡超时。。。。。。。。。。。。')
                    # logger.info('b5后发送c6指令：{}'.format(c6))
                    # self.socket_client.send(bytes.fromhex(c6))
                    continue
                c1 = CommandSendSet.combine_c1(obuid)
                logger.info('b5后发送c1指令：{}'.format(c1))
                self.socket_client.send(bytes.fromhex(c1))

                self.etc_charge_flag = True
                self.monitor_rsu_status_on = True  # 打开心跳检测
                result['flag'] = True
                result['data'] = self.command_recv_set
                result['error_msg'] = None
                return result
            else:
                logger.info('未能解析到的指令：{}'.format(msg_str))
                time.sleep(1)


    def card_sn_in_blacklist(self):
        """
        黑名单查询
        :return:
        """
        issuer_identifier = self.command_recv_set.info_b4['IssuerIdentifier']  # 发行商代码 8字节
        card_net = self.command_recv_set.info_b4['CardNetNo']    # 卡片网络编号，2字节
        # 平台参数下载-发行方黑名单接口：针对某些card_net不进行etc
        if ThirdEtcApi.exists_in_fxf_blacklist(card_net):
            return True, 'card_net: {} in blacklist'.format(card_net)
        # TODO 待确认
        card_sn = self.command_recv_set.info_b4['UserCardNo']  # card id 8字节
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
        balance = self.command_recv_set.info_b5['CardRestMoney']
        # 交易前余额 1999918332 单位分
        trans_before_balance = self.command_recv_set.info_b4['CardRestMoney']
        if CommonConf.ETC_CONF_DICT['debug'] == 'true':
            deduct_amount = 0.01
        else:
            deduct_amount = body.deduct_amount

        card_net_no = self.command_recv_set.info_b4['CardNetNo']  # 网络编号
        # ETC 卡片类型 16 储值卡  17 记账卡，转换成十进制分别对应22,23
        card_type = str(int(self.command_recv_set.info_b4['CardType'], 16))
        # PSAM 卡编号 10字节
        try:
            psam_id = self.command_recv_set.info_b4['ICCFile0015'][20: 40]
        except:
            print(self.command_recv_set.info_ba)
        #  card_sn 物理卡号 8字节
        card_sn = self.command_recv_set.info_b4['UserCardNo']
        # TODO 待确认
        logger.info('ETC 卡片类型（22:储值卡；23:记账卡）: {}'.format(card_type))
        params = dict(algorithm_type="1",
                      # TODO 金额位数待确定
                      balance=CommonUtil.hex_to_etcfee(balance, unit='fen'),  # 交易后余额
                      # TODO 待确认
                      card_net_no=card_net_no,  # 网络编号
                      card_rnd=CommonUtil.random_str(8),  # 卡内随机数
                      card_serial_no=self.command_recv_set.info_b5['ETCTradNo'],  # 卡内交易序号
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
                      issuer_identifier=self.command_recv_set.info_b4['IssuerIdentifier'].upper(),  # 发行商代码
                      obu_id=self.command_recv_set.info_b4['ObuID'].upper(),  # OBU 序号编码
                      park_code=self.rsu_conf['park_code'],  # 车场编号
                      park_record_time=park_record_time,  # 停车时长,时间精确到秒， 6小时50分钟
                      plate_color_code=body.plate_color_code,  # 车牌颜色编码 0:蓝色、1:黄色、2:黑色、3:白色、4:渐变绿色、5:黄绿双拼、6:绿色、7:蓝白渐变
                      plate_no=body.plate_no,  # 车牌号码 "皖LX4652",
                      plate_type_code=body.plate_type_code,  # 车辆类型编码 0:小车 1:大车 2:超大车
                      psam_id=psam_id,  # PSAM 卡编号 "37010101000000295460"
                      psam_serial_no=self.command_recv_set.info_b5['PSAMTransSerial'],  # PSAM 流水号 "00005BA2",
                      receivable_total_amount=CommonUtil.yuan_to_fen(body.receivable_total_amount),  # 应收金额
                      serial_number=self.command_recv_set.info_b4['ApplySerial'],  # 合同序列号"340119126C6AFEDE"
                      tac=self.command_recv_set.info_b5['TAC'],  # 交易认证码
                      terminal_id=self.command_recv_set.info_b5['PsamTerminalID'],  # 终端编号
                      trans_before_balance=CommonUtil.hex_to_etcfee(trans_before_balance, unit='fen'),  # 交易前余额 1999918332 单位分
                      trans_order_no=body.trans_order_no,  # 交易订单号 "6711683258167489287"
                      # TODO 待确认
                      trans_type='09',  # 交易类型（06:传统；09:复合）
                      vehicle_type=str(int(self.command_recv_set.info_b4['VehicleClass']))  # 收费车型
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
        #                                                                body.discount_amount, body.deduct_amount,
        #                                                                payTime)
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
        # 天线开关关闭
        self.rsu_on_or_off = StatusFlagConfig.RSU_OFF
        # 关闭天线指令
        c4 = CommandSendSet.combine_c4('00')
        logger.info('关闭天线：%s' % (c4))
        self.socket_client.send(bytes.fromhex(c4))
        # 关闭socket
        self.socket_client.shutdown(2)
        self.socket_client.close()


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
