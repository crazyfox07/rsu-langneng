# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: task_job.py
@time: 2020/10/12 9:37
"""
from common.config import CommonConf
from common.log import logger


class TimingOperateRsu(object):
    """
    定时操作天线
    """
    @staticmethod
    def turn_off_rsu():
        """
        关闭天线
        :return:
        """
        logger.info('-------------关闭天线---------------')
        for _, rsu_client in CommonConf.RSU_SOCKET_STORE_DICT.items():
            rsu_client.close_socket()

    @staticmethod
    def turn_on_rsu():
        """
        打开天线
        :return:
        """
        logger.info('-------------打开天线---------------')
        for _, rsu_client in CommonConf.RSU_SOCKET_STORE_DICT.items():
            rsu_client.init_rsu()

