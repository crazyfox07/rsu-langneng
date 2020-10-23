# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: third_db_orm.py
@time: 2020/9/8 17:46
"""

from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base


class BlackListBaseOrm(declarative_base()):
    """
    基础黑名单
    """
    __tablename__ = 'tbl_ParamInfo'
    # TODO 注意添加到表中的数据是否为都相同
    id = Column('rowid', Integer, primary_key=True, autoincrement=True)
    card_net = Column('CardNet', Integer)
    card_id = Column('CardID', String(36), index=True)
    b_list_type = Column('BListType', Integer)


class BlackListIncreOrm(declarative_base()):
    """
    增量黑名单
    """
    __tablename__ = 'tbl_ParamInfo'
    # TODO 注意添加到表中的数据是否为都相同
    id = Column('rowid', Integer, primary_key=True, autoincrement=True)
    card_net = Column('CardNet', Integer)
    card_id = Column('CardID', String(36), index=True)
    b_list_type = Column('BListType', Integer)
    status = Column('status', Integer)


if __name__ == '__main__':
    pass

