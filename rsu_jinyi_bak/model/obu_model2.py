# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: obu_model2.py
@time: 2020/10/12 14:45
"""
from pydantic import BaseModel


class OBUModel2(BaseModel):
    balance: int  # 交易后余额
    card_net_no: str  # 网络编号
    card_rnd: str  # 卡内随机数
    card_serial_no: str   # 卡内交易序号
    card_sn: str  # 物理卡号
    card_type: str  # ETC 卡片类型（22:储值卡；23:记账卡）
    charging_type: str  # 扣费方式(0:天线 1:刷卡器)
    deduct_amount: int  # 扣款金额， 单位分， 整数
    device_no: str  # 设备号
    device_type: str  # 设备类型（0:天线；1:刷卡器；9:其它）
    discount_amount: int  # 折扣金额， 单位分， 整数
    entrance_time: str  # 入场时间（yyyyMMddHHmmss）， 格式如20201012092030
    exit_time: str  # 交易时间（yyyyMMddHHmmss）
    issuer_identifier: str  # 发行商代码
    obu_id: str  # OBU 序号编码
    park_code: str  # 车场编号
    park_record_time: str  # 停车时长,时间精确到秒， 6小时50分钟20秒
    plate_color_code: str  # 车牌颜色编码 0:蓝色、1:黄色、2:黑色、3:白色、4:渐变绿色、5:黄绿双拼、6:绿色、7:蓝白渐变
    plate_no: str  # 车牌号码 "皖LX4652"
    plate_type_code: str  # 车辆类型编码 0:小车 1:大车 2:超大车
    psam_id: str  # PSAM 卡编号 "37010101000000295460"
    psam_serial_no: str  # PSAM 流水号 "00005BA2",
    receivable_total_amount: str  # 应收金额
    serial_number: str  # 合同序列号"340119126C6AFEDE"
    tac: str  # 交易认证码
    terminal_id: str  # 终端编号
    trans_before_balance: str  # 交易前余额 1999918332 单位分
    trans_order_no: str  # 交易订单号 "6711683258167489287"
    trans_type: str  # 交易类型（06:传统；09:复合）
    vehicle_type: str  # 收费车型
