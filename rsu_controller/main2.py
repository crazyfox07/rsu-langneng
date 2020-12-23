#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:main2.py
@time:2020/11/12
"""
import traceback
import os
from concurrent.futures.process import ProcessPoolExecutor

from common.config import CommonConf
from common.db_client import create_db_session
from common.log import logger
from model.db_orm import RSUInfoOrm
from service.db_operation import DBOPeration
from service.etc_toll import EtcToll
from service.soulin.rsu_socket import RsuSocket


def clear_table_rsu_info():
    """
    清空天线信息列表, 监控进程表
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


def single_process_etc_toll(etc_conf):
    # 根据车道选择天线
    # rsu0_config = etc_conf[0]
    lane_num = etc_conf['lane_num']
    park_code = etc_conf['park_code']
    sn = etc_conf['sn']
    status = 1
    # 添加天线的lane_num, park_code, heartbeat_latest,当前进程号pid，天线状态到etc_deduct.sqlite的表rsu_info中
    DBOPeration.rsu_info_to_db(lane_num, park_code, sn, os.getpid(), status)
    # 创建天线对象
    rsu_socket = RsuSocket(lane_num)
    # 进入到扣费监听状态
    EtcToll.etc_toll(rsu_socket)


def run_etc_toll():
    logger.info('。。。。。。。。。。。。。。。。。。。启动天线。。。。。。。。。。。。。。。。。。。。。。。。')
    # 先清空etc_deduct.sqlite的表rsu_info
    clear_table_rsu_info()
    if CommonConf.PROCESS_EXECUTOR:
        CommonConf.PROCESS_EXECUTOR.shutdown()
        CommonConf.PROCESS_EXECUTOR = None

    CommonConf.PROCESS_EXECUTOR = ProcessPoolExecutor(max_workers=len(CommonConf.ETC_CONF_DICT['etc']))
    for etc_conf in CommonConf.ETC_CONF_DICT['etc']:
        CommonConf.PROCESS_EXECUTOR.submit(single_process_etc_toll, etc_conf)


if __name__ == '__main__':
    run_etc_toll()