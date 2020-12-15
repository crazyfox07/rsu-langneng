import multiprocessing
import time
import uvicorn
import os
import traceback

from apscheduler import events
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from common.config import CommonConf
from common.log import logger
from model.db_orm import init_db, clear_table
from model.obu_model import OBUModel
from service.check_rsu_status import RsuStatus
from service.db_operation import DBOPeration
from service.etc_service import EtcService
from service.third_etc_api import ThirdEtcApi

app = FastAPI()

# scheduler = AsyncIOScheduler()
scheduler = BackgroundScheduler()


@app.on_event('startup')
def create_sqlite():
    """数据库初始化"""
    init_db()

# @app.on_event("startup")
# def init_rsu_store_dict():
#     """
#     初始化天线配置
#     """
#     RsuStore.init_rsu_store()
@app.on_event('startup')
def start_rsu_control():
    """
    启动天线
    @return:
    """
    RsuStatus.restart_rsu_control()


@app.on_event('startup')
def init_scheduler():
    """初始化调度器"""

    def my_listener(event):
        """事件监听"""
        if event.exception:
            logger.exception('========== The job crashed :( ==========')
            logger.exception(str(event.exception))
        else:
            logger.info('============ The job worked :) ===========')
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
    job_defaults = {
        'coalesce': True,
        'max_instances': 3
    }
    scheduler._logger = logger

    scheduler.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
    # 检测天线心跳状态， 心跳停止过长，重启天线
    scheduler.add_job(RsuStatus.check_rsu_heartbeat, trigger='cron', minute='*/3', id='check_rsu_heartbeat',
                      kwargs={'callback': ThirdEtcApi.tianxian_heartbeat}, max_instances=2)
    scheduler.add_listener(my_listener, events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR)
    logger.info("启动调度器...")

    scheduler.start()


@app.post("/etc_fee_deduction")
def etc_fee_deduction(body: OBUModel):
    """
    etc扣费
    :param body:
    :return:
    """

    body.recv_time = time.time()
    try:
        logger.info('=====================lane_num: {}  接收到扣费请求====================='.format(body.lane_num))
        DBOPeration.etc_request_info_to_db(body)
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


@app.get('/etc/deduct_status')
def etc_deduct_status(order_id: str):
    """
    查询etc扣费状态
    :param order_id: 订单号
    """
    result = EtcService.query_etc_deduct_status(order_id)
    return result


@app.get('/')
def head():
    return dict(hello='world')


if __name__ == '__main__':
    multiprocessing.freeze_support()
    # TODO workers>1时有问题，考虑gunicorn+uvicorn，同时考虑多进程的定时任务问题
    uvicorn.run(app="main:app", host="0.0.0.0", port=8001)
