import os
import sys
from concurrent.futures.thread import ThreadPoolExecutor

import yaml
from enum import Enum

def parse_ect_conf_yaml(file_path='etc_conf.yaml'):
    """
    解析etc配置文件
    :param file_path: etc配置文件路径
    :return:
    """
    with open(file_path, encoding='utf-8') as fr:
        etc_conf_dict = yaml.safe_load(fr)
        return etc_conf_dict

def app_path():
    """Returns the base application path."""
    if hasattr(sys, 'frozen'):
        # Handles PyInstaller
        # print('1111111111111111111111111111111111111111111')
        # print(getattr(sys, 'frozen'))
        # print(sys.executable)
        return os.path.dirname(sys.executable).rsplit('common')[0]  #使用pyinstaller打包后的exe目录
    return os.path.dirname(__file__).rsplit('common')[0]                 #没打包前的py目录

class CommonConf(object):
    """公共配置"""
    # etc正常扣費
    ETC_DEDUCT_FLAG = True
    # 数据帧序列号计数器
    COUNT = 0
    # 数据帧序列号8XH中X可选数值
    RSCTL = [0, 1, 2, 3, 4, 5, 6, 7, 9]
    # 指令开始标志
    COMMAND_BEGIN_FLAG = 'ffff'
    # 指令结束标志
    COMMAND_END_FLAG = 'ff'
    # 项目根目录
    # ROOT_DIR = os.path.realpath(__file__).rsplit('common')[0]
    ROOT_DIR = app_path()
    # 日志路径
    LOG_DIR = os.path.join(ROOT_DIR, 'logs')
    # etc配置文件路径
    ETC_CONF_PATH = os.path.join(ROOT_DIR, 'common', 'etc_conf.yaml')
    # etc_conf.yaml转为python的字典形式
    ETC_CONF_DICT = parse_ect_conf_yaml(ETC_CONF_PATH)
    # 超时时间
    FUNC_TIME_OUT = ETC_CONF_DICT['func_time_out']
    # socket超时时间,搜索obu的时间
    SOCKET_TIME_OUT = ETC_CONF_DICT['socket_time_out']
    # etc检测心跳超时时间
    ETC_HEARTBEAT_TIME_OUT = ETC_CONF_DICT['etc_heartbeat_time_out']
    # sqlite的路径
    SQLITE_DIR = ETC_CONF_DICT['sqlite_dir']
    # RSU状态列表
    RSU_STATUS_LIST = []
    # 天线RsuSocket存储字典
    RSU_SOCKET_STORE_DICT = dict()
    # 创建线程池
    EXECUTOR = ThreadPoolExecutor(max_workers=3)
    # wait_time_between_command
    OBU_COMMAND_WAIT_TIME = ETC_CONF_DICT['obu']['wait_time_between_command']


class StatusFlagConfig(Enum):
    # 天线状态异常
    RSU_FAILURE = 0
    # 天线状态正常
    RSU_NORMAL = 1
    # 天线开启
    RSU_ON = 2
    # 天线关闭
    RSU_OFF = 3



os.makedirs(CommonConf.LOG_DIR, exist_ok=True)
os.makedirs(CommonConf.SQLITE_DIR, exist_ok=True)



if __name__ == '__main__':
    print(CommonConf.SOCKET_TIME_OUT)
