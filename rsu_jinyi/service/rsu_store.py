# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: rsu_store.py
@time: 2020/9/17 17:20
"""
from common.config import CommonConf
from common.log import logger
from service.rsu_socket import RsuSocket


class RsuStore(object):

    @staticmethod
    def init_rsu_store():
        """
        初始化天线集合, 以车道号lane_num作为字典
        :return:
        """
        rsu_list = CommonConf.ETC_CONF_DICT['etc']
        for rsu_item in rsu_list:
            lane_num = rsu_item['lane_num']
            if lane_num not in CommonConf.RSU_SOCKET_STORE_DICT:
                rus_socket = RsuSocket(lane_num)
                CommonConf.RSU_SOCKET_STORE_DICT[lane_num] = rus_socket
                # 启动多线程监听天线状态
                CommonConf.EXECUTOR.submit(rus_socket.monitor_rsu_status, 'thread1')
        logger.info('=======================初始化天线集合=========================')




if __name__ == '__main__':
    RsuStore.init_rsu_store()