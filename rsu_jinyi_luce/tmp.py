#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:tmp.py
@time:2020/11/06
"""

import os
from concurrent.futures import ThreadPoolExecutor


def ping(i):
    result = os.popen('ping 192.168.1.{}'.format(i)).read(66)
    if result.find('字节=') != -1:
        print('192.168.1.{}'.format(i))


if __name__ == '__main__':
    excutors = ThreadPoolExecutor(max_workers=255)
    for i in range(1, 255):
        excutors.submit(ping, i)