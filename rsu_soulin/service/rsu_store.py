# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: rsu_store.py
@time: 2020/9/17 17:20
"""
from common.config import CommonConf
from common.log import logger
from service.etc_toll import EtcToll
from service.rsu_socket import RsuSocket
from concurrent.futures import ProcessPoolExecutor

executor = ProcessPoolExecutor(max_workers=2)

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
                rsu_socket = RsuSocket(lane_num)
                CommonConf.RSU_SOCKET_STORE_DICT[lane_num] = rsu_socket
                logger.info('启动多进程')
                # 启动多线程监听天线状态
                executor.submit(EtcToll.etc_toll, rsu_socket)
        logger.info('=======================初始化天线集合=========================')




if __name__ == '__main__':
    RsuStore.init_rsu_store()