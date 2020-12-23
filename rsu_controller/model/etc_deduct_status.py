#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:etc_deduct_status.py
@time:2020/12/07
"""
class EtcDeductStatus(object):
    """etc扣费状态"""
    DEDUCTING = 'deducting'   # 正在扣费
    FAIL = 'fail'  # 扣费失败
    SUCCESS = 'success'  # 扣费成功
    NO_DETECT_OBU = 'no_detect_obu'  # 没有检测到obu