import concurrent
import threading
import time

import uvicorn
import os
import traceback
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from common.config import CommonConf
from common.log import logger
from model.db_orm import init_db
from model.obu_model import OBUModel
from service.check_rsu_status import RsuStatus
from service.etc_toll import EtcToll
from service.rsu_store import RsuStore
from service.task_job import TimingOperateRsu
from service.third_etc_api import ThirdEtcApi
from threading import Thread

app = FastAPI()

# scheduler = AsyncIOScheduler()
scheduler = BackgroundScheduler()


@app.on_event("startup")
def init_rsu_store_dict():
    """
    初始化天线配置
    """
    RsuStore.init_rsu_store()


#
# @app.on_event('startup')
# def init_rsu():
#     """
#     初始化天线，主要用于心跳检测
#     :return:
#     """
#     RsuStatus.init_rsu_status_list()


@app.on_event('startup')
def create_sqlite():
    """数据库初始化"""
    init_db()


@app.on_event('startup')
def init_scheduler():
    """初始化调度器"""
    job_sqlite_path = os.path.join(CommonConf.SQLITE_DIR, 'jobs.sqlite')
    # 每次启动任务时删除数据库
    os.remove(job_sqlite_path) if os.path.exists(job_sqlite_path) else None
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///' + job_sqlite_path)  # SQLAlchemyJobStore指定存储链接
    }
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 10},  # 最大工作线程数20
        'processpool': ProcessPoolExecutor(max_workers=1)  # 最大工作进程数为5
    }

    scheduler.configure(jobstores=jobstores, executors=executors)

    # scheduler.add_job(ThirdEtcApi.my_job1, trigger='cron', minute="*/2", max_instances=2)
    # scheduler.add_job(ThirdEtcApi.my_job2, trigger='cron', minute="*/5")
    # scheduler.add_job(ThirdEtcApi.download_blacklist_base, trigger='cron', hour='1')
    # scheduler.add_job(ThirdEtcApi.download_blacklist_incre, trigger='cron', hour='*/1')

    scheduler.add_job(ThirdEtcApi.reupload_etc_deduct_from_db, trigger='cron', hour='*/1')
    scheduler.add_job(RsuStatus.monitor_rsu_heartbeat, trigger='cron', second='*/10',
                      kwargs={'callback': ThirdEtcApi.tianxian_heartbeat}, max_instances=2)
    scheduler.add_job(TimingOperateRsu.turn_off_rsu, trigger='cron', hour='0', max_instances=2)
    scheduler.add_job(TimingOperateRsu.turn_on_rsu, trigger='cron', hour='5', max_instances=2)
    logger.info("启动调度器...")

    scheduler.start()


@app.on_event("shutdown")
def shutdown():
    logger.info('application shutdown')

threadLock = threading.Lock()

@app.post("/etc_fee_deduction")
def etc_fee_deduction(body: OBUModel):
    """
    etc扣费
    :param body:
    :return:
    """

    body.recv_time = time.time()
    try:
        CommonConf.EXECUTOR.submit(EtcToll.etc_toll_by_thread, body)
        result = dict(flag=True,
                      errorCode='',
                      errorMessage='',
                      data=None)

    except:
        logger.error(traceback.format_exc())
        result = dict(flag=False,
                      errorCode='01',
                      errorMessage='etc扣费失败',
                      data=None)
    return result


@app.get('/')
def head():
    return dict(hello='world')


if __name__ == '__main__':
    # TODO workers>1时有问题，考虑gunicorn+uvicorn，同时考虑多进程的定时任务问题
    uvicorn.run(app="main:app", host="0.0.0.0", port=8001)
