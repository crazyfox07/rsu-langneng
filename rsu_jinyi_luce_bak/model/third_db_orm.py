# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: third_db_orm.py
@time: 2020/9/8 17:46
"""
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, SmallInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class BlackListBaseOrm(Base):
    """
    基础黑名单
    """
    __tablename__ = 'tbl_ParamInfo'
    # TODO 注意添加到表中的数据是否为都相同
    id = Column('rowid', Integer, primary_key=True, autoincrement=True)
    card_net = Column('CardNet', Integer)
    card_id = Column('CardID', String(36), index=True)
    b_list_type = Column('BListType', Integer)


class BlackListIncreOrm(Base):
    """
    增量黑名单
    """
    __tablename__ = 'tbl_ParamInfoIncre'
    # TODO 注意添加到表中的数据是否为都相同
    id = Column('rowid', Integer, primary_key=True, autoincrement=True)
    card_net = Column('CardNet', Integer)
    card_id = Column('CardID', String(36), index=True)
    b_list_type = Column('BListType', Integer)
    status = Column('status', Integer)


class VehicleOweOrm(Base):
    """
    欠费车辆追缴
    """
    __tablename__ = 'vehicle_owe_list'
    id = Column('id', String(32), primary_key=True)
    trans_order_no = Column('trans_order_no', String(32))  # 交易订单号
    plate_no = Column('plate_no', String(32))  # 车牌号
    plate_color = Column('plate_color', String(16))  # 车辆颜色
    plate_type_code = Column('plate_type_code', String(16))  # 车辆类型编码 0:小车 1:大车 2:超大车
    deduct_amount = Column('deduct_amount', Float)  # 扣费金额
    discount_amount = Column('discount_amount', Float)  # 折扣金额
    receivable_total_amount = Column('receivable_total_amount', Float)  # 应收金额
    entrance_time = Column('entrance_time', String(16))  # 入场时间
    exit_time = Column('exit_time', String(16))  # 出场时间
    park_record_time = Column('park_record_time', String(16))  # 停车时长
    create_time = Column('create_time', DateTime, default=datetime.now)  # now加括号的话数据都是这个固定时间


if __name__ == '__main__':
    pass

