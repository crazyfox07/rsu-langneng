#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:wuganzhifu.py
@time:2020/11/30
"""
import json
import time

from common.http_client import http_session
from common.log import logger
from common.sign_verify import XlapiSignature
from common.utils import CommonUtil
from model.db_orm import ETCRequestInfoOrm
from service.third_etc_api import ThirdEtcApi


class WuGan(object):

    @staticmethod
    def white_status(park_code, plate_no, plate_color_code):
        data_dict = {
            "method": "whiteCheck",
            "params": {
                "park_code": park_code,
                "plate_no": plate_no,
                "plate_color_code": plate_color_code
            }
        }
        data_json = json.dumps(data_dict, ensure_ascii=False)
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL,
                                data=upload_body)  # ('http://58.59.49.122:8810/api/gateway/etc', data=upload_body) #
        res_json = res.json()
        logger.info('查询白名单： data: {}, res: {}'.format(data_json, json.dumps(res_json, ensure_ascii=False)))
        white_status = res_json['data']['status']
        return white_status

    @staticmethod
    def is_white(park_code, plate_no, plate_color_code):
        white_status = WuGan.white_status(park_code, plate_no, plate_color_code)
        if white_status == '1':
            return True
        else:
            return False

    @staticmethod
    def upload_wugan(trans_order_no, park_code, plate_no, plate_color_code, plate_type_code, entrance_time,
                     park_record_time, exit_time, device_no, deduct_amount):
        entrance_time = CommonUtil.timestamp_format(entrance_time, format='%Y%m%d%H%M%S')
        exit_time = CommonUtil.timestamp_format(exit_time, format='%Y%m%d%H%M%S')
        data_dict = {
            "method": "whitePay",
            "params": {
                "trans_order_no": trans_order_no,
                "park_code": park_code,
                "plate_no": plate_no,
                "plate_color_code": plate_color_code,
                "plate_type_code": plate_type_code,
                "entrance_time": entrance_time,
                "park_record_time": park_record_time,
                "exit_time": exit_time,
                "device_no": device_no,
                "deduct_amount": deduct_amount
            }
        }

        data_json = json.dumps(data_dict, ensure_ascii=False)
        logger.info('无感支付上传： {}'.format(data_json))
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL,
                                data=upload_body)  # ('http://58.59.49.122:8810/api/gateway/etc', data=upload_body) #
        res_json = res.json()
        code, message = res_json['code'], res_json['message']
        logger.info('无感支付上传： code: {}， message: {}'.format(code, message))
        return code, message

    @staticmethod
    def notify_taigan(body: ETCRequestInfoOrm):
        logger.info('无感支付通知抬杆。。。。。。。。。。。')
        payTime = CommonUtil.timestamp_format(int(time.time()), format='%Y-%m-%d %H:%M:%S')
        res_etc_deduct_notify_flag = ThirdEtcApi.etc_deduct_notify(body.park_code, body.trans_order_no,
                                                                   body.discount_amount, body.deduct_amount, payTime)



if __name__ == '__main__':
    print(WuGan.is_white('371104', '鲁L71R86', '0'))
    # WuGan.upload_wugan('da9059253e174a50b737b37cb444214q', '371104', '鲁L71R81', '0', '0', '20201130095000',
    #                    1, '20201130095100', '0002', 0)
