# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: etc_toll.py
@time: 2020/9/2 11:24
"""
import time
import traceback
import json
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import and_

from common.config import CommonConf, StatusFlagConfig
from common.db_client import create_db_session
from common.log import logger
from common.utils import CommonUtil
from model.db_orm import RSUInfoOrm, ETCRequestInfoOrm
from model.obu_model import OBUModel
from service.db_operation import DBOPeration
from service.db_rsu_charge import DBRsuCharge
from service.rsu_socket import RsuSocket


class EtcToll(object):
    @staticmethod
    def etc_toll(rsu_client: RsuSocket):
        while True:
            now = datetime.now()
            # 查询天线的计费状态，charge=1开启计费，charge=0关闭计费
            rsu_charge = DBRsuCharge.query_rsu_charge()
            if rsu_charge == 0:
                rsu_client.rsu_heartbeat_time = now  # 更新心跳
                DBOPeration.update_rsu_heartbeat(rsu_client)  # 心跳更新入库
                time.sleep(30)
                continue
            if 0 <= now.hour <= 4:  # 0:00-4:00
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
            # 检测到obu, 检测到obu时，会狂发b2指令，频繁的更新数据库，所以此种情况下不要更新天线心跳时间
            logger.info('lane_num:{}  接收到指令: {}'.format(rsu_client.lane_num, msg_str))
            # 查询数据库订单
            _, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                              sqlite_database='etc_deduct.sqlite')
            query_item: ETCRequestInfoOrm = db_session.query(ETCRequestInfoOrm).filter(
                and_(ETCRequestInfoOrm.lane_num == rsu_client.lane_num,
                     ETCRequestInfoOrm.create_time > (datetime.now() - timedelta(seconds=10)),
                     ETCRequestInfoOrm.flag == 0)).first()
            # 找到订单开始扣费
            if query_item:
                logger.info('开始扣费。。。。。。')
                logger.info('{}, {}'.format(query_item.create_time, query_item.flag))
                etc_result = EtcToll.toll(query_item, rsu_client)
                logger.info(json.dumps(etc_result, ensure_ascii=False))
                query_item.flag = 1
                # 数据修改好后提交
                try:
                    db_session.commit()
                except:
                    db_session.rollback()
                    logger.error(traceback.format_exc())
                if etc_result['flag']:
                    logger.info('...................扣费成功........................')
                else:
                    logger.info('...................扣费失败........................')
            else:  # 没有查询到订单，pass
                pass
            db_session.close()

    @staticmethod
    # @func_set_timeout(CommonConf.FUNC_TIME_OUT)
    def toll(body: ETCRequestInfoOrm, rsu_client: RsuSocket) -> dict:
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
                                          orderNo=params['trans_order_no'],
                                          outTradeNo=params['trans_order_no'],
                                          payFee=params['deduct_amount'] / 100,
                                          derateFee=params['discount_amount'],
                                          payTime=pay_time)
                    # result['data'] = '交易成功'
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
    obumodel = OBUModel()
    obumodel.lane_num = '1'
    obumodel.deduct_amount = 0.01
    result = EtcToll.toll(obumodel)
