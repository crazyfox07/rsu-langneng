import multiprocessing
import time

import uvicorn
import os
import traceback
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, UploadFile, File

from common.config import CommonConf
from common.log import logger
from model.db_orm import init_db, clear_table
from model.obu_model import OBUModel
from service.check_rsu_status import RsuStatus
from service.db_operation import DBOPeration
from service.rsu_store import RsuStore
from service.third_etc_api import ThirdEtcApi

app = FastAPI()

# scheduler = AsyncIOScheduler()
scheduler = BackgroundScheduler()


@app.on_event('startup')
def create_sqlite():
    """数据库初始化"""
    init_db()
    # 清空表 rsu_info
    clear_table()


@app.on_event("startup")
def init_rsu_store_dict():
    """
    初始化天线配置
    """
    RsuStore.init_rsu_store()


# @app.on_event('startup')
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

    # scheduler.add_job(ThirdEtcApi.download_blacklist_base, trigger='cron', hour='1')
    # scheduler.add_job(ThirdEtcApi.download_blacklist_incre, trigger='cron', hour='*/1')

    scheduler.add_job(ThirdEtcApi.reupload_etc_deduct_from_db, trigger='cron', hour='*/1')
    scheduler.add_job(RsuStatus.upload_rsu_heartbeat, trigger='cron', minute='*/1',
                      kwargs={'callback': ThirdEtcApi.tianxian_heartbeat}, max_instances=2)
    logger.info("启动调度器...")

    scheduler.start()


@app.post("/upload/vehicle_owe")
def upload_vehicle_owe_list(file: UploadFile = File(...)):
    """
    上传etc扣费数据
    files = [('file', open('D:\logs\etc扣费异常.txt', 'rb')),]
    requests.post('http://127.0.0.1:8001/upload/vehicle_owe', files=files)
    """
    contents = file.file.read()
    file_path = os.path.join(CommonConf.ETC_CONF_DICT['sqlite_dir'], file.filename)
    with open(file_path, 'wb') as fw:
        fw.write(contents)
    return {"filename": file.filename}


@app.get('/')
def head():
    return dict(hello='world')


if __name__ == '__main__':
    multiprocessing.freeze_support()
    # TODO workers>1时有问题，考虑gunicorn+uvicorn，同时考虑多进程的定时任务问题
    uvicorn.run(app="main:app", host="0.0.0.0", port=8001)
