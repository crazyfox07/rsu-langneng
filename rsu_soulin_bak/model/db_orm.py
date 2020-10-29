# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: db_orm.py
@time: 2020/9/3 17:52
"""
from datetime import datetime
from sqlalchemy import Column, String, SmallInteger, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

from common.config import CommonConf
from common.db_client import create_db_session


db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR, sqlite_database='etc_deduct.sqlite')
Base = declarative_base()


class ETCFeeDeductInfoOrm(Base):
    __tablename__ = 'etc_fee_deduct_info'
    # TODO 注意添加到表中的数据是否为都相同
    id = Column('id', String(32), primary_key=True)
    trans_order_no = Column('trans_order_no', String(32), unique=True)
    etc_info = Column('etc_info', String(1024))
    upload_flag = Column('upload_flag', SmallInteger)
    upload_fail_count = Column('upload_fail_count', Integer)
    create_time = Column('create_time', DateTime, default=datetime.now)  # now加括号的话数据都是这个固定时间


def init_db():
    """初始化表"""
    Base.metadata.create_all(db_engine)


def delete_table_all():
    """删除所有数据库表"""
    Base.metadata.drop_all(db_engine)


if __name__ == '__main__':
    # import json
    init_db()
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

