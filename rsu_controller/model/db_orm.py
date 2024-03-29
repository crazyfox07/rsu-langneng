# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: db_orm.py
@time: 2020/9/3 17:52
"""
import traceback
from datetime import datetime
from sqlalchemy import Column, String, SmallInteger, DateTime, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base

from common.config import CommonConf
from common.db_client import create_db_session
from common.log import logger

db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR, sqlite_database='etc_deduct.sqlite')
Base = declarative_base()


class ETCFeeDeductInfoOrm(Base):
    __tablename__ = 'etc_fee_deduct_info'
    # TODO 注意添加到表中的数据是否为都相同
    id = Column('id', String(32), primary_key=True)
    trans_order_no = Column('trans_order_no', String(32))
    etc_info = Column('etc_info', String(1024))
    upload_flag = Column('upload_flag', SmallInteger)
    upload_fail_count = Column('upload_fail_count', Integer)
    create_time = Column('create_time', DateTime, default=datetime.now)  # now加括号的话数据都是这个固定时间


class ETCRequestInfoOrm(Base):
    __tablename__ = 'etc_request_info'
    id = Column('id', String(32), primary_key=True)
    lane_num = Column('lane_num', String(32))
    trans_order_no = Column('trans_order_no', String(32))
    park_code = Column('park_code', String(16))
    plate_no = Column('plate_no', String(32))
    plate_color_code = Column('plate_color_code', String(16))
    plate_type_code = Column('plate_type_code', String(16))
    entrance_time = Column('entrance_time', Integer)
    park_record_time = Column('park_record_time', Integer)
    exit_time = Column('exit_time', Integer)
    deduct_amount = Column('deduct_amount', Float)
    receivable_total_amount = Column('receivable_total_amount', Float)
    discount_amount = Column('discount_amount', Float)
    is_white = Column('is_white', SmallInteger, default=0)
    flag = Column('flag', SmallInteger, default=0)  # flag=1表示扣费成功或扣费失败，fLag=0表示没有收到obu，没有etc扣费
    deduct_status = Column('deduct_status', String(32), default='deducting')  # deducting正在扣费，fail扣费失败，success扣费成功
    create_time = Column('create_time', DateTime, default=datetime.now)  # now加括号的话数据都是这个固定时间
    update_time = Column('update_time', DateTime, default=datetime.now)  # now加括号的话数据都是这个固定时间


class RSUInfoOrm(Base):
    __tablename__ = 'rsu_info'
    id = Column('id', String(32), primary_key=True)
    lane_num = Column('lane_num', String(32))
    park_code = Column('park_code', String(16))
    sn = Column('sn', String(32))
    heartbeat_latest = Column('heartbeat_latest', DateTime)  # 天线的最新心跳时间
    pid = Column('pid', Integer)  # 天线对应程序的进程号
    status = Column('status', SmallInteger, default=1)  # 1 表示正常， 0表示天线状态异常
    create_time = Column('create_time', DateTime, default=datetime.now)


class RsuChargeOnOffOrm(Base):
    """
    开启或关闭天线收费
    """
    __tablename__ = 'rsu_charge_on_off'
    id = Column('id', String(32), primary_key=True)
    charge = Column('charge', SmallInteger, default=1)  # 1表示计费， 0表示不计费
    update_time = Column('update_time', DateTime)


def init_db():
    """初始化表"""
    Base.metadata.create_all(db_engine)

def clear_table():
    """
    清空数据表
    """
    _, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                      sqlite_database='etc_deduct.sqlite')
    try:
        db_session.query(RSUInfoOrm).delete()
        db_session.commit()
    except:
        db_session.rollback()
        logger.error(traceback.format_exc())
    finally:
        db_session.close()


def delete_table_all():
    """删除所有数据库表"""
    Base.metadata.drop_all(db_engine)


if __name__ == '__main__':
    # import json
    init_db()
    clear_table()
    # data = {
    #     "lane_num": "1",  # chedaohao
    #     "trans_order_no": "7861300266476411030",
    #     "park_code": "371151",
    #     "plate_no": "鲁Q9VS52",
    #     "plate_color_code": "0",
    #     "plate_type_code": "0",
    #     "entrance_time": 1599206869,
    #     "park_record_time": 485,
    #     "exit_time": 1599207354,
    #     "deduct_amount": 0.01,
    #     "receivable_total_amount": 0.01,
    #     "discount_amount": 0
    # }
    # etc_info = json.dumps(data)
    # print(len(etc_info))
    # import time
    # for i in range(5):
    #     time.sleep(1)
    #     etc_fee_deduct_orm = ETCFeeDeductInfoOrm(
    #         id=CommonUtil.random_str(32).lower(),
    #         etc_info=etc_info,
    #         upload_flag=1,
    #     )
    #     db_session.add(etc_fee_deduct_orm)
    #     db_session.commit()
    #     print(i)

