# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: obu_command_test.py
@time: 2020/9/16 9:52
"""
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from service.command_receive_set import CommandReceiveSet
from service.command_send_set import CommandSendSet

executor = ThreadPoolExecutor(max_workers=3)

class ObuCommandTest(object):
    """
    obu命令测试
    """

    def __init__(self, ip, port):
        """
        初始化
        :param ip:
        :param port:
        """
        # 创建一个客户端的socket对象
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接服务端
        self.client.connect((ip, port))
        # 创建命令收集对象，用于后期解析天线发送过来的命令
        self.command_recv_set = CommandReceiveSet()


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('2222222222222222222222222')
        self.close_socket()

    def test_c0(self, thread_name):
        print('===================' + thread_name + '=======================')
        # time.sleep(10)
        # return thread_name
        # 发送c0初始化指令，以二进制的形式发送数据，所以需要进行编码
        c0 = CommandSendSet.combine_c0(lane_mode='04', wait_time='02', tx_power='08', pll_channel_id='00', trans_mode='02')
        print('发送c0指令： %s' % (c0,))
        self.client.send(bytes.fromhex(c0))
        while True:
            # 接收数据
            msg_bytes = self.client.recv(1024)
            msg_str = msg_bytes.hex()  # 字节转十六进制
            if msg_str == '':
                print(thread_name + ':  null')
                break
            print('111', thread_name + ':  ' + msg_str)

    def close_socket(self):
        self.client.shutdown(2)
        self.client.close()



if __name__ == '__main__':
    # obu_command = ObuCommandTest(ip='192.168.1.69', port=60001)
    # obu_command.test_c0()
    # obu_command.close_socket()
    print('111111111111')
    a1 = ObuCommandTest(ip='192.168.1.69', port=60001)
    a1.test_c0('thread1')
    # a2 = ObuCommandTest(ip='192.168.1.69', port=60001)
    # obj1 = executor.submit(a1.test_c0, 'thread1')
    # obj2 = executor.submit(a2.test_c0, 'thread2')

    # obj_list = [obj1, obj2]
    # for future in as_completed(obj_list):
    #     data = future.result()
    #     print(f"main: {data}")
    a1.close_socket()
    a2.close_socket()
    print('over')