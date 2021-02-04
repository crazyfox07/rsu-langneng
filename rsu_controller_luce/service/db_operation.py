# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: db_operation.py
@time: 2020/10/28 8:55
"""
from datetime import datetime

from common.config import CommonConf
from common.db_client import create_db_session, DBClient
from common.log import logger
from common.utils import CommonUtil
from model.db_orm import ETCRequestInfoOrm, RSUInfoOrm
from model.obu_model import OBUModel
from service.rsu_socket import RsuSocket


class DBOPeration(object):
    @staticmethod
    def etc_request_info_to_db(body: OBUModel):
        """
        请求体body入库
        """
        db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                                  sqlite_database='etc_deduct.sqlite')
        # etc_deduct_info_json入库
        DBClient.add(db_session=db_session,
                     orm=ETCRequestInfoOrm(id=CommonUtil.random_str(32).lower(),
                                           lane_num=body.lane_num,
                                           trans_order_no=body.trans_order_no,
                                           park_code=body.park_code,
                                           plate_no=body.plate_no,
                                           plate_color_code=body.plate_color_code,
                                           plate_type_code=body.plate_type_code,
                                           entrance_time=body.entrance_time,
                                           park_record_time=body.park_record_time,
                                           exit_time=body.exit_time,
                                           deduct_amount=body.deduct_amount,
                                           receivable_total_amount=body.receivable_total_amount,
                                           discount_amount=body.discount_amount,
                                           flag=0,
                                           ))
        db_session.close()
        db_engine.dispose()

    @staticmethod
    def rsu_info_to_db(lane_num, park_code, sn, pid, status):
        """
        天线数据入库
        """
        db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                                  sqlite_database='etc_deduct.sqlite')

        DBClient.add(db_session=db_session,
                     orm=RSUInfoOrm(id=CommonUtil.random_str(32).lower(),
                                    lane_num=lane_num,
                                    park_code=park_code,
                                    sn=sn,
                                    heartbeat_latest=datetime.now(),
                                    pid=pid,
                                    status=status
                                    ))
        db_session.close()
        db_engine.dispose()

    @staticmethod
    def update_rsu_heartbeat(rsu_client: RsuSocket):
        """
        更新天线心跳时间
        """
        db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                                  sqlite_database='etc_deduct.sqlite')
        query_item: RSUInfoOrm = db_session.query(RSUInfoOrm).filter(RSUInfoOrm.lane_num == rsu_client.lane_num).first()
        query_item.heartbeat_latest = rsu_client.rsu_heartbeat_time
        # 数据修改好后提交
        try:
            db_session.commit()
        except:
            db_session.rollback()
        db_session.close()

    @staticmethod
    def update_rsu_pid_status(rsu_client: RsuSocket, status):
        """
        :param status: 1 表示天线正常工作， 0表示异常
        """
        logger.info('lane_num: {} 出现异常'.format(rsu_client.lane_num))
        db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
                                                  sqlite_database='etc_deduct.sqlite')
        query_item: RSUInfoOrm = db_session.query(RSUInfoOrm).filter(RSUInfoOrm.lane_num == rsu_client.lane_num).first()
        query_item.status = status
        # 数据修改好后提交
        try:
            db_session.commit()
        except:
            db_session.rollback()
        db_session.close()


