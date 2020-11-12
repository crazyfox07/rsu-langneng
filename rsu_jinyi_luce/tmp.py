#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:tmp.py
@time:2020/11/06
"""
import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor


def ping(i):
    result = os.popen('ping 192.168.1.{}'.format(i)).read(66)
    if result.find('字节=') != -1:
        print('192.168.1.{}'.format(i))

def func2(name, age):
    print('2222222')
    time.sleep(3)
    print('-----name: {}, age: {}------'.format(name, age))
    print('3333333333')


def func1():
    print('11111111111')
    threading.Thread(target=func2, args=('tom', 20)).start()
    print('4444444444')


if __name__ == '__main__':
    func1()
    # excutors = ThreadPoolExecutor(max_workers=255)
    # for i in range(1, 255):
    #     excutors.submit(ping, i)