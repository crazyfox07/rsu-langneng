import time

from pydantic import BaseModel


class OBUModel(BaseModel):
    """
    obu信息body体
    """
    # 车道号
    lane_num: str
    # 交易订单号
    trans_order_no: str
    park_code: str  # 车场编号（注意每个停车场一个编号，正式上线由系统分配）
    plate_no: str  # 车牌号码
    plate_color_code: str  # 车牌颜色编码 0:蓝色、1:黄色、2:黑色、3:白色、4:渐变绿色、5:黄绿双拼、6:绿色、7:蓝白渐变
    plate_type_code: str  # 车辆类型编码 0:小车 1:大车 2:超大车
    entrance_time: int  # 入场时间 精确到秒的10位时间戳
    park_record_time: int  # 停车时长,时间精确到秒
    exit_time: int  # 交易时间 精确到秒的10位时间戳
    deduct_amount: float  # 扣款金额
    receivable_total_amount: float  # 应收金额
    discount_amount: float  # 折扣金额
    recv_time = time.time()  # 接受请求的时间



if __name__ == '__main__':
    pass