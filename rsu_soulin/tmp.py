#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:tmp.py
@time:2020/11/16
"""
import os
import signal
import time
from concurrent.futures import ProcessPoolExecutor
import multiprocessing



def now():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time())))


def kill_process_by_pid(pid):
    print('**********************************************************')
    print('kill pid: {}'.format(pid))
    os.kill(pid)


def func1(i, p1):
    count = 0
    print('{}: func1'.format(i))
    while True:
        time.sleep(2)
        print('time: {}, process: {}, pid: {}'.format(now(), i, os.getpid()))
        data = dict(process_no=i,
                    pid = os.getpid())
        p1.send(data)
        count += 1
        if count > 3 and i == 0:
            pid = os.getpid()
            kill_process_by_pid(pid)




def func2(i, p0):
    count = 0
    print('{}: func2'.format(i))
    while True:
        # time.sleep(2)
        data = p0.recv()
        process_no, pid = data['process_no'], data['pid']
        print('recv : process_no: {}, pid: {}'.format(process_no, pid))
        # if process_no == 0 and count > 5:
        #     print('结束进程： process_no: {}, pid: {}'.format(process_no, pid))
        #     kill_process_by_pid(pid)
        #
        # count += 1

        # print('time: {}, process: {}, pid: {}, ppid: {}'.format(now(), i, os.getpid(), os.getppid()))
        # count += 1
        # if count > 5:
        #     print('结束进程： {}'.format(i))
        #     os._exit(0)


if __name__ == '__main__':
    # 创建一个管道　这个管道是双向的
    PIPE_SEND, PIPE_RECV = multiprocessing.Pipe()

    works = 2
    excutor = ProcessPoolExecutor(max_workers=works + 1)
    for i in range(works):
        excutor.submit(func1, i, PIPE_SEND)
    excutor.submit(func2, 2, PIPE_RECV)

    time.sleep(7)
    print('=================================')
    # print(queue.all)
    # print(os.popen('tasklist').read())
    # os.system('taskkill /IM chrome.exe /F')
    # queue.put(dict(number=1, pid=os.getpid()))
    # queue.put(dict(number=1, pid=os.getpid()))
    # time.sleep(1)
    # print(queue.qsize(), queue.)
    # while not queue.empty():
    #     print(queue.get())
