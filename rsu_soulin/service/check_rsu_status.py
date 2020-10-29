# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: check_rsu_status.py
@time: 2020/9/15 15:32
"""
import time
import traceback
import socket
import datetime
from func_timeout import func_set_timeout

from common.config import CommonConf, StatusFlagConfig
from common.db_client import create_db_session
from common.log import logger
from model.db_orm import RSUInfoOrm
from service.command_receive_set import CommandReceiveSet
from service.command_send_set import CommandSendSet
from service.rsu_socket import RsuSocket


class RsuStatus(object):
    @staticmethod
    def upload_rsu_heartbeat(callback):
        """
        上传天线心跳
        : callback: 回调函数
        :return:
        """
        _, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                                  sqlite_database='etc_deduct.sqlite')

        # 定义要上传的天线心跳字典
        upload_rsu_heartbeat_dict = dict(park_code=CommonConf.ETC_CONF_DICT['etc'][0]['park_code'],
                                         dev_code=CommonConf.ETC_CONF_DICT['dev_code'], # 设备编号，运行本代码的机器编号，非天线
                                         status_code='11',  # 11：正常，00：暂停收费，01：故障， 默认正常
                                         rsu_broke_list=[],
                                         black_file_version='0',
                                         black_file_version_incr='0'
                                         )
        query_items = db_session.query(RSUInfoOrm).all()
        now = datetime.datetime.now()
        # 读取天线配置文件
        rsu_conf_list = CommonConf.ETC_CONF_DICT['etc']
        for rsu_item in query_items:
            # 假如3分钟没有心跳，则认为天线出故障
            logger.info('距离心跳时间更新：{}s'.format((now - rsu_item.heartbeat_latest).seconds))
            if (now - rsu_item.heartbeat_latest).seconds > 60 * 3:
                rsu_conf = next(filter(lambda item: item['lane_num'] == rsu_item.lane_num, rsu_conf_list))
                upload_rsu_heartbeat_dict['rsu_broke_list'].append(rsu_conf['sn'])  # 天线sn编号

        if upload_rsu_heartbeat_dict['rsu_broke_list']:
            upload_rsu_heartbeat_dict['status_code'] = '01'
            logger.info('天线 {} 出现故障'.format(','.join(upload_rsu_heartbeat_dict['rsu_broke_list'])))
        callback(upload_rsu_heartbeat_dict)


if __name__ == '__main__':
    RsuStatus.upload_rsu_heartbeat(None)
