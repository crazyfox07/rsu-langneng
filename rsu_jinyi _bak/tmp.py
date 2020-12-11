#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:tmp.py
@time:2020/11/16
"""
import multiprocessing
import os
import time
from multiprocessing.context import Process

import uvicorn
from apscheduler import events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from common.log import logger


app = FastAPI()

# scheduler = AsyncIOScheduler()
# scheduler = BlockingScheduler()
scheduler = BackgroundScheduler()


def func3():
    i = 10
    while True:
        logger.info('5555555555555')
        1 / i
        i = i - 1
        time.sleep(2)


def func2():
    logger.info('33333333333')
    Process(target=func3).start()
    logger.info('44444444444444')




def func1():
    logger.info('11111111111')
    time.sleep(3)
    a = 1 / 0
    logger.info('22222222222')


@app.on_event('startup')
def run():
    func2()
    def my_listener(event):
        """事件监听"""
        if event.exception:
            logger.exception('========== The job crashed :( ==========')
            logger.exception(str(event.exception))
        else:
            logger.info('============ The job worked :) ===========')

    job_sqlite_path = os.path.join('sqlite_db', 'jobs.sqlite')
    # 每次启动任务时删除数据库
    os.remove(job_sqlite_path) if os.path.exists(job_sqlite_path) else None
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///' + job_sqlite_path)  # SQLAlchemyJobStore指定存储链接
    }
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 10},  # 最大工作线程数20
        'processpool': ProcessPoolExecutor(max_workers=3)  # 最大工作进程数为5
    }

    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }

    scheduler.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults)

    # scheduler.add_job(ThirdEtcApi.download_blacklist_base, trigger='cron', hour='1')
    # scheduler.add_job(ThirdEtcApi.download_blacklist_incre, trigger='cron', hour='*/1')

    # scheduler.add_job(ThirdEtcApi.reupload_etc_deduct_from_db, trigger='cron', hour='*/1')
    scheduler.add_job(func1, trigger='cron', second='*/5', id='func1')

    scheduler.add_listener(my_listener, events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR)


    logger.info("启动调度器...")

    scheduler.start()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    # TODO workers>1时有问题，考虑gunicorn+uvicorn，同时考虑多进程的定时任务问题
    uvicorn.run(app="tmp:app", host="0.0.0.0", port=8001)