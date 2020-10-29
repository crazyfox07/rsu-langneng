import time
import traceback

import uvicorn
import json
from fastapi import FastAPI

from common.config import CommonConf
from common.db_client import create_db_session, DBClient
from common.http_client import http_session
from common.log import logger
from common.sign_verify import XlapiSignature
from common.utils import CommonUtil
from model.db_orm import ETCFeeDeductInfoOrm
from model.obu_model import OBUModel
from model.obu_model2 import OBUModel2
from service.third_etc_api import ThirdEtcApi

app = FastAPI()


@app.post("/upload/etc_fee_deduction")
def upload_etc_fee_deduction(body: OBUModel2):
    """
    上传etc扣费信息
    :param body:
    :return:
    """
    logger.info('===============接收etc扣费上传请求===============')
    logger.info(body.json(ensure_ascii=False))
    params = json.loads(body.json())
    sign_combine = 'card_net_no:{},card_serial_no:{},card_sn:{},card_type:{},exit_time:{},obu_id:{},park_code:{},' \
                   'plate_no:{},tac:{}'. format(body.card_net_no, body.card_serial_no, body.card_sn, body.card_type,
                                                body.exit_time, body.obu_id, body.park_code, body.plate_no, body.tac)
    print(sign_combine)
    sign = XlapiSignature.to_sign_with_private_key(
        text=sign_combine, private_key=CommonConf.ETC_CONF_DICT['thirdApi']['private_key']).decode(encoding='utf8')
    print(sign)
    etc_deduct_info_dict = {"method": "etcPayUpload",
                            "params": params}
    # 业务编码报文json格式
    # etc_deduct_info_json = json.dumps(etc_deduct_info_dict, ensure_ascii=False)
    # # 上传etc扣费数据
    # upload_flag, upload_fail_count = ThirdEtcApi.etc_deduct_upload(etc_deduct_info_json)
    # db_engine, db_session = create_db_session(sqlite_dir=CommonConf.SQLITE_DIR,
    #                                           sqlite_database='etc_deduct.sqlite')
    # # etc_deduct_info_json入库
    # DBClient.add(db_session=db_session,
    #              orm=ETCFeeDeductInfoOrm(id=CommonUtil.random_str(32).lower(),
    #                                      trans_order_no=body.trans_order_no,
    #                                      etc_info=etc_deduct_info_json,
    #                                      upload_flag=upload_flag,
    #                                      upload_fail_count=upload_fail_count))
    # db_session.close()
    # db_engine.dispose()

    result = dict(flag=True,
                  errorCode='',
                  errorMessage='',
                  data=None)
    upload_flag = True if body.obu_id != '0' else False
    if not upload_flag:
        result['flag'] = False
        result['errorCode'] = '1'
        result['errorMessage'] = 'etc扣费上传失败'
    return result


def etc_toll_by_thread(body: OBUModel):
    time.sleep(2)
    # TODO 进行到此步骤，表示etc扣费成功，调用强哥接口
    payTime = CommonUtil.timestamp_format(int(time.time()), format='%Y-%m-%d %H:%M:%S')
    etc_deduct_notify_data = {
        "flag": True,
        "data": {
            "parkCode": body.park_code,
            "outTradeNo": body.trans_order_no,
            "derateFee": body.discount_amount,
            "payFee": body.deduct_amount,
            "payTime": payTime
        }
    }
    logger.info('etc扣费下发请求:')
    logger.info(json.dumps(etc_deduct_notify_data, ensure_ascii=False))
    etc_deduct_notify_url = 'http://z250h48353.zicp.vip:80/park/etcPayDetail'
    try:
        res = http_session.post(etc_deduct_notify_url, json=etc_deduct_notify_data)
        logger.info(res.json())
        result = res.json()['result']
        if result == 'success':
            return True
    except:
        logger.error(traceback.format_exc())
    return False

@app.post("/etc_fee_deduction")
def etc_fee_deduction(body: OBUModel):
    """
    etc扣费
    :param body:
    :return:
    """
    body.recv_time = time.time()
    logger.info('===============接收etc扣费请求===============')
    logger.info(body.json(ensure_ascii=False))
    try:
        CommonConf.EXECUTOR.submit(etc_toll_by_thread, body)
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

if __name__ == '__main__':
    # TODO workers>1时有问题，考虑gunicorn+uvicorn，同时考虑多进程的定时任务问题
    uvicorn.run(app="main2:app", host="0.0.0.0", port=8001)