# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: third_etc_api.py
@time: 2020/9/8 9:57
"""
import json
import os
import traceback

from sqlalchemy import and_

from common.config import CommonConf
from common.db_client import DBClient
from common.http_client import http_session
from common.log import logger
from common.sign_verify import XlapiSignature
from common.utils import CommonUtil
from datetime import datetime, timedelta
import time

from model.db_orm import db_session, ETCFeeDeductInfoOrm


class ThirdEtcApi(object):
    # TODO 调用第三方api
    # ETC_UPLOAD_URL = 'http://{host}:{port}/api/gateway/etc'.format(
    #     host=CommonConf.ETC_CONF_DICT['thirdApi']['host'],
    #     port=CommonConf.ETC_CONF_DICT['thirdApi']['port'])
    ETC_UPLOAD_URL = CommonConf.ETC_CONF_DICT['thirdApi']['url']
    # app_id
    APPID = CommonConf.ETC_CONF_DICT['thirdApi']['app_id']
    # 私钥
    PRIVATE_KEY = CommonConf.ETC_CONF_DICT['thirdApi']['private_key']

    @staticmethod
    def my_job1():
        time.sleep(3)
        logger.info(f'{datetime.now():%H:%M:%S} Hello job1  ============== ')

    @staticmethod
    def my_job2():
        logger.info(f'{datetime.now():%H:%M:%S} Hello job2 ')

    @staticmethod
    def etc_deduct_upload(etc_deduct_info_json):
        """
        etc支付上传
        :trans_order_no: 订单号
        :etc_deduct_info_json: 待上传的数据
        :add_to_db: 是否入库
        :return:
        """
        # # 如果上传成功upload_flag=1， 上传失败upload_flag=0, 默认上传失败
        upload_flag = 0
        # 业务编码报文
        # 将data 值base64 后，使用SHA256WithRSA 计算签名
        sign = XlapiSignature.to_sign_with_private_key(etc_deduct_info_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=etc_deduct_info_json,
                           sign=sign.decode(encoding='utf8'))
        # print('+' * 30)
        logger.info('上传etc扣费数据： {}'.format(etc_deduct_info_json))
        try:
            res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
            if res.json()['code'] == '000000':
                upload_flag = 1
            logger.info(res.json())
        except:
            logger.error(traceback.format_exc())
        upload_fail_count = 0 if upload_flag else 1
        return upload_flag, upload_fail_count

    @staticmethod
    def exists_in_blacklist(issuer_identifier, card_net, card_id):
        """
        通过第三方接口查询card_net+card_sn是否在黑名单中
        :param issuer_identifier 发行商代码
        :param card_net: card网络编号
        :param card_id: card id
        :return:
        """
        data_dict = {
            "method": "blacklist",
            "params": {
                "issuer_identifier": issuer_identifier,
                "card_net": str(card_net),
                "card_sn": card_id
            }
        }
        data_json = json.dumps(data_dict, ensure_ascii=False)
        print('+=' * 50)
        print(data_json)
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        try:
            res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
            res_json = res.json()
            status = res_json['data']['status']
            exist_flag = True if str(status) == '1' else False
        except:
            logger.error(res.text)
            logger.error('查询黑名单时出现异常： '.format(traceback.format_exc()))
            exist_flag = True
        return exist_flag

    @staticmethod
    def download_blacklist_base():
        """
        下载基础黑名单, 定时每天凌晨一点跑一次
        :return:
        """
        data_dict = {
            "method": "getBlackListFile",
            "params": {
                "last_file_name": "",
                "version": "",
                "para_code": "97"
            }
        }
        data_json = json.dumps(data_dict, ensure_ascii=False)
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
        res_json = res.json()
        logger.info('下载基础黑名单： {}'.format(res_json))
        file_url = res_json['data']['file_url']
        new_version = res_json['data']['new_version']
        para_code = res_json['data']['para_code']
        file_name = res_json['data']['file_name']
        file_path = os.path.join(CommonConf.SQLITE_DIR, file_name)
        # 下载文件
        CommonUtil.download_file(url=file_url, file_path=file_path)
        # 解压下载的zip文件
        CommonUtil.unzipfile(src_file=file_path, dest_dir=CommonConf.SQLITE_DIR)

    @staticmethod
    def download_blacklist_incre():
        """
        下载增量黑名单, 定时每隔一小时跑一次
        :return:
        """
        data_dict = {
            "method": "getBlackListFile",
            "params": {
                "last_file_name": "",
                "version": "",
                "para_code": "65"
            }
        }
        data_json = json.dumps(data_dict, ensure_ascii=False)
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
        res_json = res.json()
        logger.info('下载增量黑名单： {}'.format(res_json))
        file_url = res_json['data']['file_url']
        new_version = res_json['data']['new_version']
        para_code = res_json['data']['para_code']
        file_name = res_json['data']['file_name']
        file_path = os.path.join(CommonConf.SQLITE_DIR, file_name)
        # 下载文件
        CommonUtil.download_file(url=file_url, file_path=file_path)
        # 解压下载的zip文件
        CommonUtil.unzipfile(src_file=file_path, dest_dir=CommonConf.SQLITE_DIR)

    @staticmethod
    def reupload_etc_deduct_from_db():
        """
        查找数据库中没能成功上传的数据，重新上传
        :return:
        """
        # 查询过去一天上传失败的
        query_items = db_session.query(ETCFeeDeductInfoOrm).filter(
            and_(ETCFeeDeductInfoOrm.create_time > (datetime.now() - timedelta(days=1)),
                 ETCFeeDeductInfoOrm.upload_flag == 0))
        for item in query_items:
            #  调用第三方api
            request_flag = ThirdEtcApi.etc_deduct_upload(item.etc_info)
            if request_flag:  # 如果上传成功，更新upload_flag为1
                item.upload_flag = 1
            else:  # 如果上传失败，更新upload_fail_count 加 1
                item.upload_fail_count += 1
            # 数据修改好后提交
            try:
                db_session.commit()
            except:
                db_session.rollback()
                logger.error(traceback.format_exc())

    @staticmethod
    def tianxian_heartbeat(params):
        """
        天线心跳
        :return:
        """
        data_dict = {
            "method": "heartbeat",
            "params": params
        }
        data_json = json.dumps(data_dict, ensure_ascii=False)
        logger.info('上传天线心跳状态：{}'.format(data_json))
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
        command = res.json()['command']
        # 00：暂停收费
        # 11：正常收费（默认）
        if command == '00':
            CommonConf.ETC_CONF_PATH = False
            logger.info('暂停收费')
        elif (command is None) or (command == '11'):
            CommonConf.ETC_CONF_PATH = True
        logger.info(res.json())

    @staticmethod
    def etc_deduct_notify(parkCode, outTradeNo, derateFee, payFee, payTime):
        """
        etc扣费下发通知
        :return:
        """
        etc_deduct_notify_data = {
            "flag": True,
            "data": {
                "parkCode": parkCode,
                "outTradeNo": outTradeNo,
                "derateFee": derateFee,
                "payFee": payFee,
                "payTime": payTime
            }
        }
        print('etc扣费下发请求')
        print(etc_deduct_notify_data)
        etc_deduct_notify_url = CommonConf.ETC_CONF_DICT['thirdApi']['etc_deduct_notify_url']
        try:
            res = http_session.post(etc_deduct_notify_url, json=etc_deduct_notify_data)
            result = res.json()['result']
            if result == 'success':
                return True
        except:
            logger.error(traceback.format_exc())
        return False


if __name__ == '__main__':
    print('start')
    ThirdEtcApi.etc_deduct_notify('371104', '33ujwhdfsuh2389fsfd', 0, 0.01, "2020-09-25 00:00:00")
    # query_items = db_session.query(ETCFeeDeductInfoOrm).filter(
    #     and_(ETCFeeDeductInfoOrm.create_time > (datetime.now() - timedelta(seconds=3600)),
    #          ETCFeeDeductInfoOrm.upload_flag == 0))
    # for item in query_items:
    #     print(item.create_time, type(item.create_time), item.create_time + timedelta(seconds=36000)< datetime.now())
    # print(ThirdEtcApi.exists_in_blacklist('1' * 16, '1111', '22222222222222222222'))
    # ThirdEtcApi.download_blacklist_base()
    # ThirdEtcApi.download_blacklist_incre()
    # ThirdEtcApi.reupload_etc_deduct_from_db()
    #     etc_deduct_info_dict = {
    #     "method": "etcPayUpload",
    #     "params": {
    #         "algorithm_type": "1",
    #         "balance": 4294964440,
    #         "card_net_no": "3401",
    #         "card_rnd": "45TGUM2W",
    #         "card_serial_no": "001d",
    #         "card_sn": "1901230202361703",
    #         "card_type": "23",
    #         "charging_type": "0",
    #         "deduct_amount": 1,
    #         "device_no": "ShowLinx - 3202001001",
    #         "device_type": "0",
    #         "discount_amount": 0,
    #         "entrance_time": "20200910090150",
    #         "exit_time": "20200910091559",
    #         "issuer_identifier": "C9BDB6AB37010001",
    #         "obu_id": "014E7E95",
    #         "park_code": "371104",
    #         "park_record_time": "1分40秒",
    #         "plate_color_code": "4",
    #         "plate_no": "鲁LD10103",
    #         "plate_type_code": "0",
    #         "psam_id": "37011901230202361703",
    #         "psam_serial_no": "0000053c",
    #         "receivable_total_amount": 1,
    #         "serial_number": "3701011925377913",
    #         "tac": "5232d485",
    #         "terminal_id": "01110004dea0",
    #         "trans_before_balance": 4294964441,
    #         "trans_order_no": "1818620411622008754",
    #         "trans_type": "09",
    #         "vehicle_type": "1"
    #     }
    # }
    #     # TODO 存数据库
    #     DBClient.add(db_session=db_session,
    #                  orm=ETCFeeDeductInfoOrm(id=CommonUtil.random_str(32).lower(),
    #                                          etc_info=json.dumps(etc_deduct_info_dict, ensure_ascii=False),
    #                                          upload_flag=0,
    #                                          upload_fail_count=1))

    end = time.time()
