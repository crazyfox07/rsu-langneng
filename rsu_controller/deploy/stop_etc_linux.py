#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:stop_etc_linux.py
@time:2021/09/09
"""
import os
import re


def stop_etc():
    res = os.popen('ps -ef | grep main.py').readlines()
    pids = [next(re.finditer(r'\d+', item, re.S)).group() for item in res]
    cmd = 'kill -9 {}'.format(' '.join(pids))
    print(cmd)
    os.system(cmd)


if __name__ == '__main__':
    stop_etc()