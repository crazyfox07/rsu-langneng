#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:config_model.py
@time:2021/03/01
"""
from pydantic import BaseModel


class ConfigModel(BaseModel):
    """
    配置信息body体
    """
    # 车道号
    lane_num: str
    park_code: str  # 停车场编号
    ip: str = None  # 天线ip
    port: int = None  # 天线端口
    tx_power: int = None  # 天线功率，十进制
    pll_channel_id: str = None # 信道号
    work_mode: str = None  # 值为0标识表示正常模式，同一个标签最短20秒交易一次。
    device_no: str = None  # 设备号 32位
    device_type: str = None # 设备类型（0:天线；1:刷卡器；9:其它）
    sn: str = None  # 天线sn编号
    park_code: str = None  # 车场编号（注意每个停车场一个编号，正式上线由系统分配）
    recv_time: str = None # 接受请求的时间


if __name__ == '__main__':
    pass