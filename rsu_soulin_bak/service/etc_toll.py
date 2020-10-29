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
        print(result)

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
        try:
            # etc开始扣费，并解析天线返回的数据
            try:
                msg = rsu_client.fee_deduction(body)
            finally:
                rsu_client.monitor_rsu_status_on = True  # 恢复开启心跳检测
            # 如果扣费失败
            if (type(msg) is dict) and (msg['flag'] is False):
                result['errorMessage'] = msg['error_msg']
            elif rsu_client.etc_charge_flag:  # 表示交易成功
                # etc扣费成功后做进一步数据解析
                handle_data_result = rsu_client.handle_data(body)
                result['flag'] = handle_data_result['flag']
                result['errorMessage'] = handle_data_result['error_msg']
                params = handle_data_result['data']
                # handle_data_result['flag']=Falase一般是存在黑名单
                if handle_data_result['flag'] and handle_data_result['data']:
                    # 交易时间格式转换
                    pay_time = CommonUtil.timeformat_convert(timestr1=params['exit_time'], format1='%Y%m%d%H%M%S',
                                                             format2='%Y-%m-%d %H:%M:%S')
                    result['data'] = dict(parkCode=params['park_code'],
                                          orderNo=params['trans_order_no'],
                                          outTradeNo=params['trans_order_no'],
                                          payFee=params['deduct_amount'] / 100,
                                          derateFee=params['discount_amount'],
                                          payTime=pay_time)
                    # result['data'] = '交易成功'
                    data = dict(method='etcPayUpload',
                                params=params, )
                    logger.info('etc交易成功')
                    logger.info(json.dumps(data, ensure_ascii=False))

            else:
                logger.error("etc扣费失败")
        except:
            logger.error(traceback.format_exc())
        # 记入日志
        logger.info(json.dumps(result, ensure_ascii=False))
        return result




if __name__ == '__main__':
    obumodel = OBUModel()
    obumodel.lane_num = '1'
    obumodel.deduct_amount = 0.01
    result = EtcToll.toll(obumodel)
