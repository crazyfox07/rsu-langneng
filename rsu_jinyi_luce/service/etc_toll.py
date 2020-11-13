# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: etc_toll.py
@time: 2020/9/2 11:24
"""
import pickle
import threading
import time
import traceback
import json
from datetime import datetime


from common.config import CommonConf
from common.db_client import DBClient
from common.log import logger
from common.utils import CommonUtil
from model.third_db_orm import VehicleOweOrm
from service.db_operation import DBOPeration
from service.rsu_socket import RsuSocket
from service.third_etc_api import ThirdEtcApi



class EtcToll(object):
    @staticmethod
    def etc_toll(rsu_client: RsuSocket):
        """
        根据检测到的obu信息判断是否扣费
        @param rsu_client:
        @return:
        """

        while True:
            # socket监听，接受数据
            try:
                msg_str = rsu_client.recv_msg_max_wait_time()
            except:
                err_msg = traceback.format_exc()
                logger.error(err_msg)
                if err_msg.find('远程主机强迫关闭了一个现有的连接') != -1 or err_msg.find('你的主机中的软件中止了一个已建立的连接') != -1:
                    time.sleep(30)
                else:
                    time.sleep(10)
                continue
            # 有接收到数据，表明天线还在工作，更新心跳时间
            rsu_client.rsu_heartbeat_time = datetime.now()
            if msg_str[8: 12] == 'b200':  # 心跳指令
                logger.info('lane_num:{}  心跳指令：{}， 天线时间：{}， 当前时间：{}'.format(rsu_client.lane_num, msg_str,
                                                                            rsu_client.rsu_heartbeat_time,
                                                                            datetime.now()))
                DBOPeration.update_rsu_heartbeat(rsu_client)  # 心跳更新入库
                continue
            elif msg_str[8: 12] == 'b201':
                logger.error('射频初始化异常： {}'.format(msg_str))
                break
            elif msg_str[8: 12] == 'b202':
                logger.error('PSAM卡初始化异常或无卡： {}'.format(msg_str))
                break
            elif msg_str[8: 10] == 'b4':
                logger.info('检测到车辆信息')
                logger.info(msg=msg_str)
                b4_info = rsu_client.command_recv_set.parse_b4(msg_str)
                plate_no = b4_info['VehicleLicencePlateNumber']
                plate_color = b4_info['VehicleLicencePlateColor']

                # TODO 待删
                # if (plate_no == 'ffffffffffffffffffffffff' and plate_color == 'ffff') or \
                #         (plate_no == '000000000000000000000000' and plate_color == '0000'):  # 测试卡
                #     logger.info('测试卡：{}'.format(msg_str))
                #     logger.info('b4信息： {}'.format(json.dumps(b4_info)))
                #     plate_no, plate_color = 'd4c141313131313100000000', '0000'

                plate_no = CommonUtil.parse_plate_code(plate_no)
                logger.info('车牌号： {}， 车颜色：{}'.format(plate_no, plate_color))
                park_code = rsu_client.rsu_conf['park_code']  # 停车场
                # 上传车辆信息
                threading.Thread(target=ThirdEtcApi.upload_vehicle_plate_no,
                                 args=(park_code, plate_no, plate_color)).start()
                # TODO 该处为测试，待删，扣所有obu的车费
                if plate_no:
                    plate_no_test = '鲁L12345'
                    query_vehicle_owe: VehicleOweOrm = DBClient.query_vehicle_owe(plate_no_test, plate_color)  # 查询欠费车辆信息
                    query_vehicle_owe.plate_no = plate_no
                else:
                    query_vehicle_owe = None

                # TODO 待恢复
                # query_vehicle_owe: VehicleOweOrm = DBClient.query_vehicle_owe(plate_no, plate_color)  # 查询欠费车辆信息


                if query_vehicle_owe:  # 如果车辆欠费，开启扣费
                    logger.info('-------------车牌号：{}， 车颜色：{} 欠费，开始扣费----------'.format(plate_no, plate_color))
                    # etc_result = rsu_client.fee_deduction(body)
                    etc_result = EtcToll.toll(query_vehicle_owe, rsu_client)
                    if etc_result['flag'] is True:
                        logger.info('------------------------扣费成功--------------------------')
                        # TODO 后续成功扣费后需要删除数据库中的数据
                    else:
                        logger.error('------------------------扣费失败--------------------------')

                else:
                    logger.info('车牌号：{}， 车颜色：{} 没有欠费'.format(plate_no, plate_color))

            else:
                logger.info('lane_num:{}  接收到指令: {}'.format(rsu_client.lane_num, msg_str))
                if not msg_str:
                    time.sleep(3)

    @staticmethod
    # @func_set_timeout(CommonConf.FUNC_TIME_OUT)
    def toll(body: VehicleOweOrm, rsu_client: RsuSocket) -> dict:
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
        try:
            # etc开始扣费，并解析天线返回的数据
            msg = rsu_client.fee_deduction(body)
            # 如果扣费失败
            if msg['flag'] is False:
                result['errorMessage'] = msg['error_msg']
            else:  # 表示交易成功
                # etc扣费成功后做进一步数据解析
                handle_data_result = rsu_client.handle_data(body)
                result['flag'] = handle_data_result['flag']
                result['errorMessage'] = handle_data_result['error_msg']
                params = handle_data_result['data']
                # handle_data_result['flag']=False一般是存在黑名单
                if handle_data_result['flag'] and handle_data_result['data']:
                    # 交易时间格式转换
                    pay_time = CommonUtil.timeformat_convert(timestr1=params['exit_time'], format1='%Y%m%d%H%M%S',
                                                             format2='%Y-%m-%d %H:%M:%S')
                    result['data'] = dict(parkCode=params['park_code'],
                                          payFee=params['deduct_amount'] / 100,
                                          payTime=pay_time)
                    data = dict(method='etcPayUpload',
                                params=params, )
                    logger.info('etc交易成功')
                    logger.info(json.dumps(data, ensure_ascii=False))

        except:
            logger.error(traceback.format_exc())
        # 记入日志
        logger.info(json.dumps(result, ensure_ascii=False))
        return result




if __name__ == '__main__':
    # obumodel = OBUModel()
    # obumodel.lane_num = '1'
    # obumodel.deduct_amount = 0.01
    # result = EtcToll.toll(obumodel)
    # TimingJob.pull_vehicle_owe_list()
    with open(CommonConf.VEHICLE_OWE_FILE_PATH.replace('txt', 'pkl'), 'rb') as fr:
        obj = pickle.load(fr)
        print(obj)