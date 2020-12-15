#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:etc_service.py
@time:2020/12/07
"""
from datetime import datetime
from common.config import CommonConf
from common.db_client import create_db_session
from model.db_orm import ETCRequestInfoOrm
from model.etc_deduct_status import EtcDeductStatus


class EtcService(object):
    @staticmethod
    def query_etc_deduct_status(order_id: str) -> dict:
        """
        查询etc扣费状态
        :param order_id: 订单号
        """
        result = {
            "flag": False,
            "errorCode": "",
            "errorMessage": "",
            "data": None
        }

        _, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                          sqlite_database='etc_deduct.sqlite')
        etc_request_orm: ETCRequestInfoOrm = db_session.query(ETCRequestInfoOrm).filter(
            ETCRequestInfoOrm.trans_order_no == order_id).first()
        if etc_request_orm:
            deduct_status = etc_request_orm.deduct_status
            result['data'] = deduct_status
            if deduct_status == EtcDeductStatus.SUCCESS:
                result['flag'] = True
            elif deduct_status == EtcDeductStatus.DEDUCTING:
                create_time = etc_request_orm.create_time
                if (datetime.now() - create_time).seconds > 10:  # 超过10s还是DEDUCTING，认为没有检测到obu
                    result['data'] = EtcDeductStatus.NO_DETECT_OBU
        else:
            msg = '没有此订单号: {}'.format(order_id)
            result['data'] = msg
            result['errorMessage'] = msg
        return result
