# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: db_client.py
@time: 2020/9/3 16:59
"""
import os
import traceback
from common.config import CommonConf
from sqlalchemy import create_engine, Index, and_
from sqlalchemy.orm import sessionmaker
from common.log import logger
from model.third_db_orm import BlackListBaseOrm, BlackListIncreOrm


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
    engine = create_engine('sqlite:///' + sqlite_path)
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
            logger.info('数据入库成功')
        except:
            db_session.rollback()
            logger.error(traceback.format_exc())

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


if __name__ == '__main__':
    # print(os.path.exists(CommonConf.ETC_CONF_DICT['sqlite_dir']))
    import time

    # # 解压下载的zip文件
    # CommonUtil.unzipfile(src_file=r'E:\lxw\sqlite_db\70090901_GBCardBList.cfg.zip', dest_dir=CommonConf.SQLITE_DIR)
    # begin = time.time()
    # DBClient.create_index_on_cardid()
    # end = time.time()
    # print('time use: %ss, exists_flag: %s'%(int(end) - int(begin), 1))


    for item in range(10):
        begin = time.time()
        exists_flag =DBClient.exists_in_blacklist('1102', '080823003003762' + str(item))

        end = time.time()
        print('time use: %ss, exists_flag: %s, item: %s'%(int(end) - int(begin), exists_flag, item))
        exists_flag = DBClient.exists_in_blacklist(3701, '1942230216041231' + str(item))
        print('time use: %ss, exists_flag: %s' % (int(time.time()) - int(end), exists_flag))
