# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: etc_toll.py
@time: 2020/9/2 11:24
"""
import random
import time
import traceback
import json
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from func_timeout import func_set_timeout
from sqlalchemy import and_

from common.config import CommonConf, StatusFlagConfig
from common.db_client import create_db_session
from common.log import logger
from common.utils import CommonUtil
from model.db_orm import ETCRequestInfoOrm
from model.etc_deduct_status import EtcDeductStatus
from service.db_operation import DBOPeration
from service.db_rsu_charge import DBRsuCharge
from service.rsu_socket import RsuSocket


# class TimingJob(object):

    # @staticmethod
    # def start_scheduler(rsu_client: RsuSocket):
    #     logger.info('++++++++++++++++++++++++++++++++++++++++++++++')
    #     scheduler = BackgroundScheduler()
    #     scheduler.add_job(TimingJob.check_rsu_status, args=(rsu_client,), trigger='cron', minute='*/1')  # 每一分钟检查一次天线状态
    #     logger.info('lane_num: {} 启动定时任务'.format(rsu_client.lane_num))
    #     scheduler.start()

    # @staticmethod
    # def check_rsu_status(rsu_client):
    #     """
    #     检查天线状态，心跳时间过长重启天线
    #     """
    #     _, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
    #                                       sqlite_database='etc_deduct.sqlite')
    #     rsu_info: RSUInfoOrm = db_session.query(RSUInfoOrm).filter(RSUInfoOrm.lane_num == rsu_client.lane_num).first()
    #     # 如果三分钟内没有更新心跳，重启天线
    #     if (datetime.now() - rsu_info.heartbeat_latest).seconds > 60 * 3:
    #         rsu_client.rsu_status = StatusFlagConfig.RSU_FAILURE
    #         logger.info('lane_num: {} 心跳不正常，数据库中最新心跳时间: {}， 对象的最新心跳时间： {}'.format(
    #             rsu_client.lane_num, rsu_info.heartbeat_latest, rsu_client.rsu_heartbeat_time))
    #         try:
    #             rsu_client.init_rsu()
    #         except:
    #             logger.error(traceback.format_exc())
    #         if rsu_client.rsu_status == StatusFlagConfig.RSU_FAILURE:
    #             logger.info('**********重启天线失败**************')
    #         else:
    #             logger.info('**********重启天线成功**************')
    #             rsu_info.heartbeat_latest = rsu_client.rsu_heartbeat_time
    #             try:
    #                 db_session.commit()
    #             except:
    #                 db_session.rollback()
    #                 logger.error('重启天线后，更新数据库失败')
    #     else:
    #         logger.info('lane_num: {}， 心跳正常，数据库中最新心跳时间: {}， 对象的最新心跳时间： {}'.format(
    #             rsu_client.lane_num, rsu_info.heartbeat_latest, rsu_client.rsu_heartbeat_time))
    #     db_session.close()
from service.wuganzhifu import WuGan


class EtcToll(object):
    @staticmethod
    def etc_toll(rsu_client: RsuSocket):
        # TimingJob.start_scheduler(rsu_client)
        while True:
            time.sleep(random.choice(range(2, 12)))
            now = datetime.now()
            # 查询天线的计费状态，charge=1开启计费，charge=0关闭计费
            rsu_charge = DBRsuCharge.query_rsu_charge()

            # 有接收到数据，表明天线还在工作，更新心跳时间
            rsu_client.rsu_heartbeat_time = datetime.now()
            DBOPeration.update_rsu_heartbeat(rsu_client)  # 心跳更新入库

            # 查询数据库订单
            _, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                              sqlite_database='etc_deduct.sqlite')
            query_item: ETCRequestInfoOrm = db_session.query(ETCRequestInfoOrm).filter(
                and_(ETCRequestInfoOrm.lane_num == rsu_client.lane_num,
                     ETCRequestInfoOrm.create_time > (datetime.now() - timedelta(seconds=10)),
                     ETCRequestInfoOrm.flag == 0)).first()
            # TODO  收到etc扣费请求，但是车上没有obu
            # 找到订单开始扣费
            if query_item:
                logger.info('开始扣费。。。。。。')
                logger.info('{}, {}'.format(query_item.create_time, query_item.flag))
                etc_result = EtcToll.toll(query_item, rsu_client)

                etc_result['flag'] = False if random.randint(0,1) == 0 else True
                query_item.flag = 1

                if etc_result['flag']:
                    logger.info('...................扣费成功........................')
                    query_item.deduct_status = EtcDeductStatus.SUCCESS
                else:
                    logger.info('...................扣费失败........................')
                    query_item.deduct_status = EtcDeductStatus.FAIL
                # 数据修改好后提交
                try:
                    db_session.commit()
                except:
                    db_session.rollback()
                    logger.error(traceback.format_exc())

            else:
                # 没有查询到订单，pass
                pass
            db_session.close()


    @staticmethod
    @func_set_timeout(CommonConf.FUNC_TIME_OUT)
    def toll(body: ETCRequestInfoOrm, rsu_client: RsuSocket) -> dict:
        """
        etc收费
        :param body: 接收到的数据
        :param rsu_client: socket客户端
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
            # 如果扣费失败，同时无感支付开启，并且是白名单，开启无感支付
            if (msg['flag'] is False) and (CommonConf.ETC_CONF_DICT['wugan'] == 'true') and (body.is_white == 1):
                device_no = CommonConf.ETC_CONF_DICT['dev_code']
                deduct_amount = CommonUtil.yuan_to_fen(body.deduct_amount)
                park_code = CommonConf.ETC_CONF_DICT['etc'][0]['park_code']
                code, message = WuGan.upload_wugan(body.trans_order_no, park_code, body.plate_no,
                                                   body.plate_color_code, body.plate_type_code, body.entrance_time,
                                                   body.park_record_time, body.exit_time, device_no, deduct_amount)
                if code == '000000':
                    WuGan.notify_taigan(body)
                    result['flag'] = True
                    result['errorMessage'] = None
                else:
                    result['errorCode'] = code
                    result['errorMessage'] = message
            elif msg['flag'] is False:
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
        except:
            logger.error(traceback.format_exc())
        # 记入日志
        logger.info(json.dumps(result, ensure_ascii=False))
        return result




if __name__ == '__main__':
    # 查询数据库订单
    _, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                      sqlite_database='etc_deduct.sqlite')
    query_item: ETCRequestInfoOrm = db_session.query(ETCRequestInfoOrm).filter(
        and_(ETCRequestInfoOrm.lane_num == '002',
             ETCRequestInfoOrm.create_time > (datetime.now() - timedelta(seconds=12000)),
             ETCRequestInfoOrm.flag == 0)).order_by(ETCRequestInfoOrm.create_time.desc()).first()

    # 找到订单开始扣费
    if query_item:
        logger.info('开始扣费。。。。。。')
        logger.info('{}, {}'.format(query_item.create_time, query_item.flag))
        query_item.flag = 3
        # 数据修改好后提交
        try:
            db_session.commit()
        except:
            db_session.rollback()
            logger.error(traceback.format_exc())
        logger.info('...................扣费成功........................')
    else:
        logger.info('........监听心跳........')

    db_session.close()
