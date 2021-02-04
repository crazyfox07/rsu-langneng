#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:main2.py
@time:2020/11/12
"""
import traceback
import os
from common.config import CommonConf
from common.db_client import create_db_session
from common.log import logger
from model.db_orm import RSUInfoOrm
from service.db_operation import DBOPeration
from service.etc_toll import EtcToll
from service.rsu_socket import RsuSocket


def clear_table_rsu_info():
    """
    清空天线信息列表
    @return:
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


def run_etc_toll():
    logger.info('。。。。。。。。。。。。。。。。。。。启动天线。。。。。。。。。。。。。。。。。。。。。。。。')
    # 先清空etc_deduct.sqlite的表rsu_info
    clear_table_rsu_info()

    # 根据车道选择天线
    rsu0_config = CommonConf.ETC_CONF_DICT['etc'][0]
    lane_num = rsu0_config['lane_num']
    park_code = rsu0_config['park_code']
    sn = rsu0_config['sn']
    status = 1
    # 添加天线的lane_num, park_code, heartbeat_latest,当前进程号pid，天线状态到etc_deduct.sqlite的表rsu_info中
    DBOPeration.rsu_info_to_db(lane_num, park_code, sn, os.getpid(), status)
    # 创建天线对象
    rsu_socket = RsuSocket(lane_num)
    # 进入到扣费监听状态
    EtcToll.etc_toll(rsu_socket)


if __name__ == '__main__':
    run_etc_toll()