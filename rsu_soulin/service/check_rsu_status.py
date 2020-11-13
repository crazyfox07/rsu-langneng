# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: check_rsu_status.py
@time: 2020/9/15 15:32
"""
import datetime

import main2
from common.config import CommonConf
from common.db_client import create_db_session
from common.log import logger
from model.db_orm import RSUInfoOrm

from multiprocessing import Process


class RsuStatus(object):

    @staticmethod
    def restart_rsu_control():
        """
        重启天线服务
        @return:
        """
        if CommonConf.RSU_PROCESS:
            logger.info('===========重启天线============')
            CommonConf.RSU_PROCESS.terminate()
        CommonConf.RSU_PROCESS = Process(target=main2.run_etc_toll)
        CommonConf.RSU_PROCESS.start()

    @staticmethod
    def check_rsu_heartbeat(callback):
        """
        检测天线心跳状态， 心跳停止过长，重启天线
        @return:
        """
        # 定义要上传的天线心跳字典
        upload_rsu_heartbeat_dict = dict(park_code=CommonConf.ETC_CONF_DICT['etc'][0]['park_code'],
                                         dev_code=CommonConf.ETC_CONF_DICT['dev_code'],  # 设备编号，运行本代码的机器编号，非天线
                                         status_code='11',  # 11：正常，00：暂停收费，01：故障， 默认正常
                                         rsu_broke_list=[],
                                         black_file_version='0',
                                         black_file_version_incr='0'
                                         )
        db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                                  sqlite_database='etc_deduct.sqlite')
        rsu_info_orms = db_session.query(RSUInfoOrm).all()
        now = datetime.datetime.now()
        for rsu_infor_orm in rsu_info_orms:
            time_diff_seconds = (now - rsu_infor_orm.heartbeat_latest).seconds
            # 如果三分钟没有心跳，需要重启etc扣费
            if time_diff_seconds >= 60 * 3:
                logger.error('park_code: {}, lane_num: {} 的最新心跳时间： {}，距离当前已过：{}s'.format(
                    rsu_infor_orm.park_code,
                    rsu_infor_orm.lane_num,
                    rsu_infor_orm.heartbeat_latest,
                    time_diff_seconds))
                upload_rsu_heartbeat_dict['rsu_broke_list'].append(rsu_infor_orm.sn)

        if upload_rsu_heartbeat_dict['rsu_broke_list']:
            upload_rsu_heartbeat_dict['status_code'] = '01'
            logger.error('天线 {} 出现故障'.format(','.join(upload_rsu_heartbeat_dict['rsu_broke_list'])))
            logger.info("==================重启天线服务================")
            # TODO
            RsuStatus.restart_rsu_control()
        else:
            logger.info('。。。。。。。。。天线心跳正常。。。。。。。。。')

        callback(upload_rsu_heartbeat_dict)


if __name__ == '__main__':
    RsuStatus.check_rsu_heartbeat(None)
