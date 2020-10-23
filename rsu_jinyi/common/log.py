# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: log.py
@time: 2020/9/1 8:35
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler

from common.utils import CommonUtil
from common.config import CommonConf

class Logger:
    def __init__(self, logame, logfile):
        """
        日志
        :param logame: log对象名
        :param logfile: 生成log文件路径
        """
        self.logger = logging.getLogger(logame)
        # 创建一个handler，用于写入日志文件，每隔一天分割一次日志文件
        # backupCount 是保留日志个数。默认的0是不会自动删除掉日志。若设10，则在文件的创建过程中库会判断是否有超过这个10，若超过，则会从最先创建的开始删除。
        # file_handler = TimedRotatingFileHandler(logfile, when='D', interval=1, backupCount=30)
        # 按照大小做切割       将切好的文件放到logfile     1024字节     只保留5个文件
        file_handler = RotatingFileHandler(logfile, maxBytes=1024 * 1024 * 100,backupCount=20)
        # file_handler = logging.FileHandler(logfile, mode='a')
        # 再创建一个handler, 用于输出到控制台
        console_handler = logging.StreamHandler()
        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        # 添加handler
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        # 设置日志级别
        self.logger.setLevel(logging.INFO)


log_path = os.path.join(CommonConf.LOG_DIR, 'tianxian.log')

logger = Logger("tianxian", log_path).logger


if __name__ == "__main__":
    import time
    count = 0
    while True:
        logger.info("{}".format(count))
        count += 1
        # time.sleep(0.01)

