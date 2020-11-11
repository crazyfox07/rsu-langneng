# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: db_client.py
@time: 2020/9/3 16:59
"""
import os
import re
import traceback
from common.config import CommonConf
from sqlalchemy import create_engine, Index, and_
from sqlalchemy.orm import sessionmaker
from common.log import logger
from common.utils import CommonUtil
from model.third_db_orm import BlackListBaseOrm, BlackListIncreOrm, VehicleOweOrm, Base


def create_db_session(sqlite_dir=CommonConf.SQLITE_DIR, sqlite_database='etc_deduct.sqlite'):
    """
    创建数据库session
    :return:
    """
    # mysql_info = CommonConf.ETC_CONF_DICT['mysql']
    # print(mysql_info)
    # engine = create_engine("mysql+pymysql://{username}:{password}@{host}:{port}/{db_name}?charset=utf8".format(
    #     username=mysql_info['username'], password=mysql_info['passworld'], host=mysql_info['host'],
    #     port=mysql_info['port'], db_name=mysql_info['db_name']),
    #     echo=False,  # echo参数为True时，会显示每条执行的SQL语句，可以关闭
    #     pool_size=5,  # 连接池大小
    #     )
    sqlite_path = os.path.join(sqlite_dir, sqlite_database)
    engine = create_engine('sqlite:///' + sqlite_path, connect_args={'check_same_thread': False})
    db_session = sessionmaker(bind=engine)()
    return engine, db_session


class DBClient(object):


    @staticmethod
    def create_index_on_cardid():
        """
        给基础数据库的CardID创建索引
        :return:
        """
        db_session_blacklist_db_engine, db_session_blacklist_db_base = create_db_session(
            sqlite_dir=CommonConf.SQLITE_DIR, sqlite_database='GBCardBList.cfg')
        # 先删除已有索引
        idx_tbl_ParamInfo1 = Index('idx_tbl_ParamInfo1', BlackListBaseOrm.card_net, BlackListBaseOrm.card_id)
        idx_tbl_ParamInfo1.drop(bind=db_session_blacklist_db_engine)

        # 创建索引
        blacklist_base_orm_idx = Index('blacklist_base_orm_idx', BlackListBaseOrm.card_id)
        blacklist_base_orm_idx.create(bind=db_session_blacklist_db_engine)

        db_session_blacklist_db_base.close()

    @staticmethod
    def add(db_session, orm):
        try:
            db_session.add(orm)
            db_session.commit()
        except:
            db_session.rollback()
            logger.error(traceback.format_exc())
            logger.info('数据入库失败')

    @staticmethod
    def exists_in_blacklist(card_net, card_id):
        """
        查看card_id是否存在于数据库中
        :param card_net: card网络编号
        :param card_id: card id
        :return:
        """
        # 查看增量黑名单
        _, db_session_blacklist_db_incre = create_db_session(
            sqlite_dir=CommonConf.SQLITE_DIR, sqlite_database='GBCardBListIncre.cfg')

        query_item = db_session_blacklist_db_incre.query(BlackListIncreOrm).filter(
            and_(BlackListIncreOrm.card_net == card_net, BlackListIncreOrm.card_id == card_id)).first()
        db_session_blacklist_db_incre.close()
        if query_item:
            return True

        # 查看基础黑名单
        _, db_session_blacklist_db_base = create_db_session(
            sqlite_dir=CommonConf.SQLITE_DIR, sqlite_database='GBCardBList.cfg')

        query_item = db_session_blacklist_db_base.query(BlackListBaseOrm).filter(
            and_(BlackListBaseOrm.card_net == card_net, BlackListBaseOrm.card_id == card_id)).first()
        db_session_blacklist_db_base.close()
        if query_item:
            return True

        return False

    @staticmethod
    def add_vehicle_owe_list():
        """
        添加欠费车辆到数据库中，测试用
        """
        db_engine, db_session = create_db_session(
            sqlite_dir=CommonConf.SQLITE_DIR, sqlite_database='vehicle_owe.sqlite')

        Base.metadata.create_all(db_engine)

        vehicle_owe_orm_item = VehicleOweOrm(id=CommonUtil.random_str(32),
                                             trans_order_no='123456789',
                                             plate_no='粤A11111',
                                             plate_color='0000',
                                             plate_type_code='1',
                                             deduct_amount=0.01,
                                             discount_amount=0,
                                             receivable_total_amount=0.0,
                                             entrance_time='20201109101010',
                                             exit_time='20201109105012',
                                             park_record_time='40分钟2秒')
        vehicle_owe_orm_item2 = VehicleOweOrm(id=CommonUtil.random_str(32),
                                             trans_order_no='123456788',
                                             plate_no='鲁L12345',
                                             plate_color='0000',
                                             plate_type_code='1',
                                             deduct_amount=0.00,
                                             discount_amount=0,
                                             receivable_total_amount=0.00,
                                             entrance_time='20201109101010',
                                             exit_time='20201109105012',
                                             park_record_time='40分钟2秒')
        vehicle_owe_orm_items = [vehicle_owe_orm_item, vehicle_owe_orm_item2]

        try:
            db_session.bulk_save_objects(vehicle_owe_orm_items)
            db_session.commit()
        except:
            db_session.rollback()
            logger.error(traceback.format_exc())
            logger.info('数据入库失败')

    @staticmethod
    def query_vehicle_owe(plate_no, plate_color) -> VehicleOweOrm:
        """
        根据车牌号和车牌颜色查询欠费车辆
        """
        _, db_session = create_db_session(
            sqlite_dir=CommonConf.SQLITE_DIR, sqlite_database='vehicle_owe.sqlite')
        query_result = db_session.query(VehicleOweOrm).filter(VehicleOweOrm.plate_no==plate_no,
                                                              VehicleOweOrm.plate_color==plate_color).first()
        return query_result


if __name__ == '__main__':
    DBClient.add_vehicle_owe_list()

    db_engine, db_session = create_db_session(
        sqlite_dir=CommonConf.SQLITE_DIR, sqlite_database='vehicle_owe.sqlite')
    query = DBClient.query_vehicle_owe('粤A11111', '00')
    if query:
        print(query.plate_no, query.plate_color, query.deduct_amount)
