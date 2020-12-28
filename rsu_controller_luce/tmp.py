#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:tmp.py
@time:2020/11/06
"""
import multiprocessing
from multiprocessing import Process
import time
import os
import sys
from concurrent.futures import ProcessPoolExecutor



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
    # threading.Thread(target=func2, args=('tom', 20)).start()
    time.sleep(1)
    restart_program()

    print('4444444444')


def restart_program():
    print("重启。。。。。。。")
    python = sys.executable
    os.execl(python, python, *sys.argv)

def func3():
    import re
    a = ['root         1     0  2 15:28 pts/0    00:00:05 python3 main.py\n', 'root         9     1  3 15:28 pts/0    00:00:05 python3 main.py\n', 'root        10     1  0 15:28 pts/0    00:00:00 python3 main.py\n', 'root        75    71  0 15:31 pts/1    00:00:00 /bin/sh -c ps -ef|grep main\n', 'root        77    75  0 15:31 pts/1    00:00:00 grep main\n']
    # a0 = 'root         1     0  2 15:28 pts/0    00:00:05 python3 main.py\nroot         9     1  3 15:28 pts/0    00:00:05 python3 main.py\nroot        10     1  0 15:28 pts/0    00:00:00 python3 main.py\nroot        72    71  0 15:31 pts/1    00:00:00 /bin/sh -c ps -ef|grep main\nroot        74    72  0 15:31 pts/1    00:00:00 grep main\n'
    for item in a:
        if item.find('grep') == -1:
            a1 = re.split('\s+', item)[1]
            print(a1)

def func4():
    print('00000000')
    p = Process(target=func2, args=('tom', 18))
    p.start()
    print(p.pid)
    # p.join()
    p.terminate()
    print('555555555')

if __name__ == '__main__':
    func4()
    # excutors = ThreadPoolExecutor(max_workers=255)
    # for i in range(1, 255):
    #     excutors.submit(ping, i)