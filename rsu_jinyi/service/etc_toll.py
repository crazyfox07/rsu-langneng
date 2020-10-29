# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: etc_toll.py
@time: 2020/9/2 11:24
"""
import time
import traceback
import json

from func_timeout import func_set_timeout

from common.config import CommonConf
from common.log import logger
from common.utils import CommonUtil
from model.obu_model import OBUModel
from service.rsu_socket import RsuSocket


class EtcToll(object):
    @staticmethod
    def etc_toll_by_thread(body: OBUModel):
        begin = time.time()
        result = EtcToll.toll(body)
        logger.info('etc扣费结束，用时: {}s'.format(time.time() - begin))
        logger.info(result)

    @staticmethod
    @func_set_timeout(CommonConf.FUNC_TIME_OUT)
    def toll(body: OBUModel) -> dict:
        """
        etc收费
        :param body: 接收到的数据
        :return:
        """
        # 默认扣费失败
        result = dict(flag=False,
                      errorCode='01',
                      errorMessage='etc扣费失败',
                      data=None)
        if not CommonConf.ETC_DEDUCT_FLAG:
            return result

        rsu_client: RsuSocket = CommonConf.RSU_SOCKET_STORE_DICT[body.lane_num]  # RsuSocket(body.lane_num)
        # etc开始扣费，并解析天线返回的数据
        try:
            msg = rsu_client.fee_deduction(body)
            logger.info(msg)
            if msg['data']:
                logger.info(msg['data'].info_b4)
                logger.info(msg['data'].info_b5)
            logger.info('over')
            if msg['flag'] == True:
                # etc扣费成功后做进一步数据解析
                rsu_client.handle_data(body)
            else:
                logger.error(json.dumps(msg))
        except:
            logger.error(traceback.format_exc())
        finally:
            rsu_client.monitor_rsu_status_on = True  # 恢复开启心跳检测
            # 记入日志
            return result




if __name__ == '__main__':
    obumodel = OBUModel()
    obumodel.lane_num = '1'
    obumodel.deduct_amount = 0.01
    result = EtcToll.toll(obumodel)
