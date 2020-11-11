# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: etc_toll.py
@time: 2020/9/2 11:24
"""
import pickle
import time
import traceback
import json
import re
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from common.config import CommonConf, StatusFlagConfig
from common.db_client import create_db_session, DBClient
from common.log import logger
from common.utils import CommonUtil
from model.db_orm import RSUInfoOrm
from model.third_db_orm import VehicleOweOrm
from model.vehicle_owe_model import VehicleOweModel
from service.db_operation import DBOPeration
from service.rsu_socket import RsuSocket


class TimingJob(object):
    @staticmethod
    def start_scheduler(rsu_client: RsuSocket):
        logger.info('++++++++++++++++++++++++++++++++++++++++++++++')
        scheduler = BackgroundScheduler()
        scheduler.add_job(TimingJob.check_rsu_status, args=(rsu_client,), trigger='cron', minute='*/1')  # 每一分钟检查一次天线状态
        scheduler.add_job(TimingJob.pull_vehicle_owe_list, trigger='cron', hour='0,12')  # 拉取车辆欠费名单
        logger.info('lane_num: {} 启动定时任务'.format(rsu_client.lane_num))
        scheduler.start()

    @staticmethod
    def check_rsu_status(rsu_client):
        """
        检查天线状态，心跳时间过长重启天线
        """
        _, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                          sqlite_database='etc_deduct.sqlite')
        rsu_info: RSUInfoOrm = db_session.query(RSUInfoOrm).filter(RSUInfoOrm.lane_num == rsu_client.lane_num).first()
        # 如果三分钟内没有更新心跳，重启天线
        if (datetime.now() - rsu_info.heartbeat_latest).seconds > 60 * 3:
            rsu_client.rsu_status = StatusFlagConfig.RSU_FAILURE
            logger.info('lane_num: {} 心跳不正常，数据库中最新心跳时间: {}， 对象的最新心跳时间： {}'.format(
                rsu_client.lane_num, rsu_info.heartbeat_latest, rsu_client.rsu_heartbeat_time))
            try:
                rsu_client.init_rsu()
            except:
                logger.error(traceback.format_exc())
            if rsu_client.rsu_status == StatusFlagConfig.RSU_FAILURE:
                logger.info('**********重启天线失败**************')
            else:
                logger.info('**********重启天线成功**************')
                rsu_info.heartbeat_latest = rsu_client.rsu_heartbeat_time
                try:
                    db_session.commit()
                except:
                    db_session.rollback()
                    logger.error('重启天线后，更新数据库失败')
        else:
            logger.info('lane_num: {}， 心跳正常，数据库中最新心跳时间: {}， 对象的最新心跳时间： {}'.format(
                rsu_client.lane_num, rsu_info.heartbeat_latest, rsu_client.rsu_heartbeat_time))
        db_session.close()

    @staticmethod
    def pull_vehicle_owe_list():
        """
        定时拉取车辆欠费名单列表
        """
        # TODO http请求下载车辆欠费名单
        logger.info('拉取车辆欠费名单, sqlite格式')
        logger.info('拉取结束')


class EtcToll(object):
    @staticmethod
    def etc_toll(rsu_client: RsuSocket):
        TimingJob.pull_vehicle_owe_list()  # 启动定时任务前先拉取车辆欠费名
        DBOPeration.rsu_info_to_db(rsu_client)
        TimingJob.start_scheduler(rsu_client)
        while True:
            now = datetime.now()
            if 0 <= now.hour < 5:  # 0:00-5:00关闭天线
                if rsu_client.rsu_on_or_off == StatusFlagConfig.RSU_ON:
                    logger.info('-------------关闭天线---------------')
                    rsu_client.close_socket()
                    rsu_client.rsu_on_or_off = StatusFlagConfig.RSU_OFF

                rsu_client.rsu_heartbeat_time = now  # 更新心跳
                DBOPeration.update_rsu_heartbeat(rsu_client)  # 心跳更新入库
                time.sleep(60)
                logger.info('。。。当前天线处于休眠状态。。。')
                continue
            elif rsu_client.rsu_on_or_off == StatusFlagConfig.RSU_OFF:  # 其它时间段打开天线
                logger.info('-------------打开天线---------------')
                rsu_client.init_rsu()
                rsu_client.rsu_on_or_off = StatusFlagConfig.RSU_ON

            # socket监听，接受数据
            try:
                msg_str = rsu_client.recv_msg_max_wait_time()
            except:
                err_msg = traceback.format_exc()
                logger.error(err_msg)
                if err_msg.find('远程主机强迫关闭了一个现有的连接') != -1 or err_msg.find('你的主机中的软件中止了一个已建立的连接') != -1:
                    time.sleep(30)
                else:
                    time.sleep(10)
                continue
            # 有接收到数据，表明天线还在工作，更新心跳时间
            rsu_client.rsu_heartbeat_time = datetime.now()
            if msg_str[8: 12] == 'b200':  # 心跳指令
                logger.info('lane_num:{}  心跳指令：{}， 天线时间：{}， 当前时间：{}'.format(rsu_client.lane_num, msg_str,
                                                                            rsu_client.rsu_heartbeat_time,
                                                                            datetime.now()))
                DBOPeration.update_rsu_heartbeat(rsu_client)  # 心跳更新入库
                continue
            elif msg_str[8: 12] == 'b201':
                logger.error('射频初始化异常： {}'.format(msg_str))
                break
            elif msg_str[8: 12] == 'b202':
                logger.error('PSAM卡初始化异常或无卡： {}'.format(msg_str))
                break
            elif msg_str[8: 10] == 'b4':
                logger.info('检测到车辆信息')
                logger.info(msg=msg_str)
                b4_info = rsu_client.command_recv_set.parse_b4(msg_str)
                plate_no = b4_info['VehicleLicencePlateNumber']
                plate_color = b4_info['VehicleLicencePlateColor']
                # TODO 待删
                # if (plate_no == 'ffffffffffffffffffffffff' and plate_color == 'ffff') or \
                #         (plate_no == '000000000000000000000000' and plate_color == '0000'):  # 测试卡
                #     logger.info('测试卡：{}'.format(msg_str))
                #     logger.info('b4信息： {}'.format(json.dumps(b4_info)))
                #     plate_no, plate_color = 'd4c141313131313100000000', '0000'
                plate_no = CommonUtil.parse_plate_code(plate_no)
                logger.info('车牌号： {}， 车颜色：{}'.format(plate_no, plate_color))

                # TODO 该处为测试，待删，扣所有obu的车费
                if plate_no:
                    plate_no_test = '鲁L12345'
                    query_vehicle_owe: VehicleOweOrm = DBClient.query_vehicle_owe(plate_no_test, plate_color)  # 查询欠费车辆信息
                    query_vehicle_owe.plate_no = plate_no
                else:
                    query_vehicle_owe = None

                # TODO 待恢复
                # query_vehicle_owe: VehicleOweOrm = DBClient.query_vehicle_owe(plate_no, plate_color)  # 查询欠费车辆信息


                if query_vehicle_owe:  # 如果车辆欠费，开启扣费
                    logger.info('-------------车牌号：{}， 车颜色：{} 欠费，开始扣费----------'.format(plate_no, plate_color))
                    # etc_result = rsu_client.fee_deduction(body)
                    etc_result = EtcToll.toll(query_vehicle_owe, rsu_client)
                    logger.info(json.dumps(etc_result))
                    if etc_result['flag'] is True:
                        logger.info('------------------------扣费成功--------------------------')
                        # TODO 后续成功扣费后需要删除数据库中的数据
                    else:
                        logger.error('------------------------扣费失败--------------------------')

                else:
                    logger.info('车牌号：{}， 车颜色：{} 没有欠费'.format(plate_no, plate_color))
            else:
                logger.info('lane_num:{}  接收到指令: {}'.format(rsu_client.lane_num, msg_str))

    @staticmethod
    # @func_set_timeout(CommonConf.FUNC_TIME_OUT)
    def toll(body: VehicleOweOrm, rsu_client: RsuSocket) -> dict:
        """
        etc收费
        :param body: 接收到的数据
        :return:
        """
        # 默认扣费失败
        result = dict(flag=False,
                      errorCode='01',
                      errorMessage='etc扣费失败',
                      data=None)
        if not CommonConf.ETC_DEDUCT_FLAG:
            return result
        try:
            # etc开始扣费，并解析天线返回的数据
            msg = rsu_client.fee_deduction(body)
            # 如果扣费失败
            if msg['flag'] is False:
                result['errorMessage'] = msg['error_msg']
            else:  # 表示交易成功
                # etc扣费成功后做进一步数据解析
                handle_data_result = rsu_client.handle_data(body)
                result['flag'] = handle_data_result['flag']
                result['errorMessage'] = handle_data_result['error_msg']
                params = handle_data_result['data']
                # handle_data_result['flag']=False一般是存在黑名单
                if handle_data_result['flag'] and handle_data_result['data']:
                    # 交易时间格式转换
                    pay_time = CommonUtil.timeformat_convert(timestr1=params['exit_time'], format1='%Y%m%d%H%M%S',
                                                             format2='%Y-%m-%d %H:%M:%S')
                    result['data'] = dict(parkCode=params['park_code'],
                                          payFee=params['deduct_amount'] / 100,
                                          payTime=pay_time)
                    data = dict(method='etcPayUpload',
                                params=params, )
                    logger.info('etc交易成功')
                    logger.info(json.dumps(data, ensure_ascii=False))

        except:
            logger.error(traceback.format_exc())
        # 记入日志
        logger.info(json.dumps(result, ensure_ascii=False))
        return result




if __name__ == '__main__':
    # obumodel = OBUModel()
    # obumodel.lane_num = '1'
    # obumodel.deduct_amount = 0.01
    # result = EtcToll.toll(obumodel)
    # TimingJob.pull_vehicle_owe_list()
    with open(CommonConf.VEHICLE_OWE_FILE_PATH.replace('txt', 'pkl'), 'rb') as fr:
        obj = pickle.load(fr)
        print(obj)