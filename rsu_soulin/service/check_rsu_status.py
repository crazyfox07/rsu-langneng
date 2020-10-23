# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: check_rsu_status.py
@time: 2020/9/15 15:32
"""
import traceback
import socket
import datetime
from func_timeout import func_set_timeout

from common.config import CommonConf, StatusFlagConfig
from common.log import logger
from service.command_receive_set import CommandReceiveSet
from service.command_send_set import CommandSendSet
from service.rsu_socket import RsuSocket


class RsuStatus(object):
    @staticmethod
    def monitor_rsu_heartbeat(callback):
        """
        监听天线心跳
        : callback: 回调函数
        :return:
        """
        # 定义要上传的天线心跳字典
        upload_rsu_heartbeat_dict = dict(park_code=CommonConf.ETC_CONF_DICT['etc'][0]['park_code'],
                                         dev_code=CommonConf.ETC_CONF_DICT['dev_code'], # 设备编号，运行本代码的机器编号，非天线
                                         status_code='11',  # 11：正常，00：暂停收费，01：故障， 默认正常
                                         rsu_broke_list=[],
                                         black_file_version='0',
                                         black_file_version_incr='0'
                                         )
        logger.info('监听心跳。。。。。。。')

        for lane_num, rsu_client in CommonConf.RSU_SOCKET_STORE_DICT.items():
            if rsu_client.rsu_on_or_off == StatusFlagConfig.RSU_OFF:
                logger.info('天线处于休眠状态')
                continue
            logger.info('++++++++++天线处于工作状态+++++++++++')
            now = datetime.datetime.now()
            # 假如三分钟没有心跳，则认为天线出故障，并重启socket
            logger.info('距离心跳时间更新：{}s'.format((now - rsu_client.rsu_heartbeat_time).seconds))
            if (now - rsu_client.rsu_heartbeat_time).seconds > 60 * 3:
                rsu_client.rsu_status = StatusFlagConfig.RSU_FAILURE
                #  重启socket
                try:
                    rsu_client.init_rsu()
                except:
                    logger.error(traceback.format_exc())
                if rsu_client.rsu_status == StatusFlagConfig.RSU_FAILURE:
                    logger.info('**********重启天线失败**************')
                    # 将出现故障的天线的sn加入到rsu_broke_list列表中
                    upload_rsu_heartbeat_dict['rsu_broke_list'].append(rsu_client.rsu_conf['sn'])
                else:
                    logger.info('**********重启天线成功**************')
            else:
                rsu_client.rsu_status = StatusFlagConfig.RSU_NORMAL
        if upload_rsu_heartbeat_dict['rsu_broke_list']:
            upload_rsu_heartbeat_dict['status_code'] = '01'
        callback(upload_rsu_heartbeat_dict)

    @staticmethod
    def init_rsu_status_list():
        """
        初始化天线状态列表
        :return:
        """

        tianxian_list = CommonConf.ETC_CONF_DICT['etc']
        for item in tianxian_list:  # 从配置文件中获取的天线列表
            tianxian_status_item = dict(park_code=item['park_code'],
                                        lane_num=item['lane_num'],
                                        sn=item['sn'],
                                        ip=item['ip'],
                                        port=item['port'],
                                        rsu_status=1,  # 天线状态,0表示正常，1表示异常， 默认异常
                                        )
            CommonConf.RSU_STATUS_LIST.append(tianxian_status_item)


    @staticmethod
    @func_set_timeout(5)
    def get_rsu_status(etc_conf):
        """
        获取天线状态
        :param ip:
        :param port:
        :return:
        """
        # 创建一个客户端的socket对象
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # 连接服务端
            client.connect((etc_conf['ip'], etc_conf['port']))
            # 发送c0初始化指令，以二进制的形式发送数据，所以需要进行编码
            c0 = CommandSendSet.combine_c0(lane_mode=etc_conf['lane_mode'], wait_time=etc_conf['wait_time'],
                                           tx_power=etc_conf['tx_power'],
                                           pll_channel_id=etc_conf['pll_channel_id'],
                                           trans_mode=etc_conf['trans_mode']).strip()
            client.send(bytes.fromhex(c0))
            # 接收数据
            msg_bytes = client.recv(1024)
            msg_str = msg_bytes.hex()  # 字节转十六进制

            command_recv_set = CommandReceiveSet()
            # b0 设备状态信息帧
            if msg_str[6: 8] == 'b0':
                command_recv_set.parse_b0(msg_str)  # 解析b0指令
                # 天线状态
                rsu_status = command_recv_set.info_b0['RSUStatus']
                return rsu_status
        except:
            logger.error(traceback.format_exc())
        finally:
            # 关闭client
            client.shutdown(2)
            client.close()


if __name__ == '__main__':
    RsuStatus.monitor_rsu_heartbeat()
