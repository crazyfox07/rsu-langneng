# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: http_client.py
@time: 2020/9/6 16:45
"""
import json
import requests

from common.config import CommonConf
from common.sign_verify import XlapiSignature


class HttpClient(object):
    """
    http客户端
    """

    def __init__(self, headers=None, **kwargs):
        self.session = requests.Session()
        self.session.headers = headers

    def get_http_session(self):
        return self.session


http_session = HttpClient().get_http_session()

if __name__ == '__main__':
    etc_deduct_info_dict = {
        "method": "etcPayUpload",
        "params": {
            "algorithm_type": "1",
            "balance": 43070,
            "card_net_no": "3702",
            "card_rnd": "75A6E727",
            "card_serial_no": "0419",
            "card_sn": "1303220100390927",
            "card_type": "22",
            "charging_type": "0",
            "deduct_amount": 0,
            "device_no": "Showlinx-0000000013",
            "device_type": "0",
            "discount_amount": 0,
            "entrance_time": "20200828104818",
            "exit_time": "20200828111728",
            "issuer_identifier": "C9BDB6AB37010001",
            "obu_id": "070C062A",
            "park_code": "371157",
            "park_record_time": "28分钟",
            "plate_color_code": "0",
            "plate_no": "鲁L12345",
            "plate_type_code": "0",
            "psam_id": "37010101000000295602",
            "psam_serial_no": "000026EC",
            "receivable_total_amount": 0,
            "serial_number": "3701071521078758",
            "tac": "CC688326",
            "terminal_id": "0137000482B2",
            "trans_before_balance": 43070,
            "trans_order_no": "1818620411622008756",
            "trans_type": "09",
            "vehicle_type": "1"
        }
    }
    # app_id
    app_id = CommonConf.ETC_CONF_DICT['thirdApi']['app_id']
    # 私钥
    private_key = CommonConf.ETC_CONF_DICT['thirdApi']['private_key']
    # 业务编码报文
    etc_deduct_info_json = json.dumps(etc_deduct_info_dict, ensure_ascii=False)
    # 将data 值base64 后，使用SHA256WithRSA 计算签名
    sign = XlapiSignature.to_sign_with_private_key(etc_deduct_info_json, private_key=private_key)
    upload_body = dict(appid=app_id,
                       data=etc_deduct_info_json,
                       sign=sign.decode(encoding='utf8'))
    print('*' * 50)
    print(json.dumps(upload_body, ensure_ascii=False))
    # pprint(upload_body)
    # pprint(json.dumps(upload_body, ensure_ascii=False))
    res = requests.post(url='http://58.59.49.122:8810/api/gateway/etc', data=upload_body)
    print(res.json())
