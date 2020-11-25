"""
使用flask框架
"""
import multiprocessing
import time

import os
import traceback
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from flask_pydantic import validate
from common.config import CommonConf
from common.log import logger
from model.db_orm import init_db, clear_table
from model.obu_model import OBUModel
from service.check_rsu_status import RsuStatus
from service.db_operation import DBOPeration
from service.rsu_store import RsuStore
from service.third_etc_api import ThirdEtcApi

from flask import Flask


def init_scheduler():
    """初始化调度器"""
    # scheduler = AsyncIOScheduler()
    scheduler = BackgroundScheduler()

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

    # scheduler.add_job(TimingOperateRsu.turn_off_rsu, trigger='cron', hour='0', max_instances=2)
    # scheduler.add_job(TimingOperateRsu.turn_on_rsu, trigger='cron', hour='5', max_instances=2)
    logger.info("启动调度器...")

    scheduler.start()

def create_app():
    logger.info('======================创建app=======================')
    # 创建app
    app = Flask(__name__)
    return app


app = create_app()

@app.route("/etc_fee_deduction", methods=['POST'])
@validate()
def etc_fee_deduction(body: OBUModel):
    """
    etc扣费
    :param body:
    :return:
    """
    print(body)
    print('11111111111111111111111')

    body.recv_time = time.time()
    try:
        DBOPeration.etc_request_info_to_db(body)
        logger.info('time use: {}'.format(time.time() - body.recv_time))
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


@app.route('/', methods=['GET'])
def head():
    return dict(hello='world')


def startup_task():
    """
    程序启动时创建初始化任务
    """
    # 数据库初始化
    init_db()
    # 清空表 rsu_info
    clear_table()
    # 初始化天线配置
    RsuStore.init_rsu_store()
    # 开启定时任务
    init_scheduler()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    startup_task()
    app.run(host='127.0.0.1', port=8001, debug=False)
