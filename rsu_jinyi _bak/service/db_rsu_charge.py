#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:db_rsu_charge.py
@time:2020/11/24
"""
from datetime import datetime

from common.config import CommonConf
from common.db_client import DBClient, create_db_session
from common.utils import CommonUtil
from model.db_orm import RsuChargeOnOffOrm


class DBRsuCharge(object):
    """
    查询或更新天线的计费状态，charge=1开启计费，charge=0关闭计费
    """
    @staticmethod
    def update_rsu_charge_on_off(charge=1, update_time=datetime.now()):
        """
        更新表rsu_charge_on_off
        """
        _, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                          sqlite_database='etc_deduct.sqlite')
        query_item: RsuChargeOnOffOrm = db_session.query(RsuChargeOnOffOrm).first()
        if query_item:
            query_item.charge = charge
            query_item.update_time = update_time
            # 数据修改好后提交
            try:
                db_session.commit()
            except:
                db_session.rollback()
            db_session.close()
        else:
            DBClient.add(db_session=db_session,
                         orm=RsuChargeOnOffOrm(id=CommonUtil.random_str(32).lower(),
                                               charge=charge,
                                               update_time=update_time))

    @staticmethod
    def query_rsu_charge():
        """
        查询是否启用天线扣费状态， rsu_charge_on_off的chage=1，开启扣费模式， charge=0，关闭扣费模式
        """
        db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                                  sqlite_database='etc_deduct.sqlite')
        query_item: RsuChargeOnOffOrm = db_session.query(RsuChargeOnOffOrm).first()
        if not query_item:
            query_item = RsuChargeOnOffOrm(id=CommonUtil.random_str(32).lower(),
                                           charge=1,
                                           update_time=datetime.now())
            DBClient.add(db_session=db_session,
                         orm=query_item)

        return query_item.charge