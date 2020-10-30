import binascii
import os
import time
import random
import string
import zipfile
import requests

from common.config import CommonConf
from datetime import datetime


class CommonUtil(object):
    @staticmethod
    def timestamp_format(timestamp=int(time.time()), format='%Y%m%d%H%M%S'):
        """
        时间戳格式化
        :param timestamp:
        :param format:
        :return:
        """
        timeformat = time.strftime(format, time.localtime(timestamp))
        return timeformat

    @staticmethod
    def str_to_timestamp(timestr='20200904155900', format='%Y%m%d%H%M%S'):
        """
        字符串转时间戳
        :param timestr:
        :param format:
        :return:
        """
        time_array = time.strptime(timestr, format)
        timestamp = int(time.mktime(time_array))
        return timestamp

    @staticmethod
    def timeformat_convert(timestr1='20200907094345', format1='%Y%m%d%H%M%S', format2='%Y-%m-%d %H:%M:%S'):
        """
        时间格式之间的转换
        :param format1: 格式1
        :param format2: 格式2
        :return:
        """
        time_array1 = time.strptime(timestr1, format1)
        timestamp1 = int(time.mktime(time_array1))
        timestr2 = time.strftime(format2, time.localtime(timestamp1))
        return timestr2

    @staticmethod
    def get_rsctl():
        """
        获取发送到天线的数据帧
        :return:
        """
        index = CommonConf.COUNT % len(CommonConf.RSCTL)
        rsctl = '8' + str(CommonConf.RSCTL[index])
        CommonConf.COUNT += 1
        return rsctl

    @staticmethod
    def bcc_xor(value_verify):
        """
        bcc 异或值校验
        :param value_verify: 待校验的值
        :return:
        """
        # 将‘ffff89’转换成['ff', 'ff', '89']
        str_to_list = [value_verify[2 * i] + value_verify[2 * i + 1] for i in range(len(value_verify) // 2)]
        bcc = int(str_to_list[0], 16)
        for item in str_to_list[1:]:
            bcc = bcc ^ int(item, 16)
        bcc = hex(bcc)[2:]
        bcc = '0' + bcc if len(bcc) == 1 else bcc
        return bcc

    @staticmethod
    def crc_jinyi(value_verify):
        """
        金益的crc校验。 CRC计算采用CRC-16/X25（x16 + x12 + x5 + 1）算法，初始值为0xFFFF。从LEN到DATA所有字节的CRC16校验值，2字节
        :param value_verify: 待校验的值， 如 'ffff0004b2000000'
        :return:
        """
        ffff = 0xffff
        crc_init = 0xffff
        value_verify_bytes = bytes.fromhex(value_verify[4:])
        for item in value_verify_bytes:
            crc_init = crc_init ^ item
            crc_init = crc_init & ffff
            for i in range(8):
                if crc_init & 0x0001:
                    crc_init = (crc_init >> 1) ^ 0x8408
                else:
                    crc_init = crc_init >> 1
        crc_init = (~crc_init) & ffff
        crc = hex(crc_init)[2:]
        zero_len = 4 - len(crc)
        crc = '0' * zero_len + crc
        return crc

    @staticmethod
    def etcfee_to_hex(consume_money):
        """
        etc费用转hex,
        :param consume_money: 消费金额
        :return:
        """
        consume_money = int(consume_money * 100)
        consume_money_hex = hex(consume_money)[2:]
        zero_pad_num = 0 if (8 - len(consume_money_hex)) < 0 else (8 - len(consume_money_hex))
        consume_money_hex = '0' * zero_pad_num + consume_money_hex
        return consume_money_hex[-8:]

    @staticmethod
    def hex_to_etcfee(consume_money_hex, unit='yuan'):
        """
        hex转etc费用
        :param consume_money_hex: etc费用的hex形式
        :return:
        """
        if unit == 'yuan':
            consume_money = int(consume_money_hex, 16) / 100
        elif unit == 'fen':
            consume_money = int(consume_money_hex, 16)
        return consume_money

    @staticmethod
    def random_str(num):
        """
        生成随机字符串
        :param num: 字符串的个数
        :return:
        """
        str_ = ''.join(random.sample(string.digits + string.ascii_uppercase, num))
        return str_

    @staticmethod
    def yuan_to_fen(money:float) -> int:
        """
        将人民币由单位元转为分
        :param money:
        :return:
        """
        return int(money * 100)

    @staticmethod
    def time_difference(timestamp1, timestamp2):
        """
        计算时间差 timestamp2 - timestamp1
        :param timestamp1: 时间戳1
        :param timestamp2: 时间戳2
        :return:
        """
        date1= datetime.fromtimestamp(timestamp1)
        date2 = datetime.fromtimestamp(timestamp2)
        time_diff = date2 - date1
        days = time_diff.days
        hours = time_diff.seconds // (60 * 60)
        minutes = (time_diff.seconds % (60 * 60)) // 60
        seconds = (time_diff.seconds % (60 * 60)) % 60
        time_diff_str = '%d分%d秒' % (minutes, seconds)
        if (days <= 0) and (hours > 0) :
            time_diff_str = '%d小时%s' % (hours, time_diff_str)
        elif days > 0:
            time_diff_str = '%d天%d小时%s' % (days, hours, time_diff_str)
        return time_diff_str

    @staticmethod
    def parse_plate_code(plate_code):
        """
        解析车牌号
        :param plate_code: 车牌号，16进制形式 b2e241313233343500000000
        :return:
        """
        return binascii.a2b_hex(plate_code).decode('gb2312').replace('\x00', '')

    @staticmethod
    def download_file(url, file_path, chunk_size=1024 * 4):
        """
        下载文件
        :param url: 请求url
        :param file_path: 文件路径
        :param chunk_size: 按块下载
        :return:
        """
        with requests.get(url, stream=True) as req:

            with open(file_path, 'wb') as f:
                for chunk in req.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

    @staticmethod
    def unzipfile(src_file, dest_dir):
        """
        解压zip文件
        :param src_file: 带解压的zip文件
        :param dest_dir: 解压后的目标目录
        :return:
        """
        zf = zipfile.ZipFile(src_file)
        zf.extractall(dest_dir)


def crc162(x, invert):
    a = 0xFFFF
    b = 0xA001
    for byte in x:
        a ^= ord(byte)
        for i in range(8):
            last = a % 2
            a >>= 1
            if last == 1:
                a ^= b
    s = hex(a).upper()

    return s[4:6] + s[2:4] if invert == True else s[2:4] + s[4:6]


def crc16(x, invert):
    a = 0xFFFF
    b = 0xA001
    for byte in x:
        a ^= byte
        for i in range(8):
            last = a % 2
            a >>= 1
            if last == 1:
                a ^= b
    print(a)
    a = (~a) & (0xffffffff)
    s = hex(a).upper()
    print(s)
    return s

if __name__ == '__main__':
    # src_file = r'E:\lxw\project\tianxian-demo\database\10908198_GBCardBListIncre.cfg.zip'
    # dest_dir = os.path.join(CommonConf.ROOT_DIR, 'database')
    # CommonUtil.unzipfile(src_file, dest_dir)
    # consume_money_hex = CommonUtil.etcfee_to_hex(999.99)
    # print(consume_money_hex)
    # consume_money = CommonUtil.hex_to_etcfee(consume_money_hex)
    # print(consume_money)
    #
    # print(CommonUtil.hex_to_etcfee('fe01fe01'))
    # print(CommonUtil.hex_to_etcfee('ffffa579'))
    #
    # ss = CommonUtil.random_str(8)
    # print(ss)
    # st1 = int(time.time())
    # st2 = st1 + 3 * 24 * 60 * 60 + 2 * 60 * 60 + 3 * 60 + 5
    # st2 = st1 + 3 * 24 * 60 * 60 + 5
    # print(CommonUtil.time_difference(1599792556, 1599792656))
    # c = int(time.time())
    # bcc = CommonUtil.crc_jinyi('ffff000db00002fbc3d610000001110600')  # ('ffff0004b2000100')
    s = 'ffff0004b2000100'
    s = 'ffff000db00002fbc3d610000001110600'
    s = 'ffff0047b502f7d5930200000d8f8d20201020164741000000006d000000000509006d08240379eac4f5350000000000000000000000000000000000000000000000000000000000000000'
    s = 'ffff0004b2000000'
    crc = CommonUtil.crc_jinyi(s)
    print(crc)
    # print(c)
    # for _ in range(10):
    #     # a = CommonUtil.timestamp_format(timestamp=c, format='%Y%m%d%H%M%S')
    #     time.sleep(1)
    #     a = CommonUtil.timestamp_format(int(time.time()))
    #     print(a)
    # b = CommonUtil.str_to_timestamp(a, format='%Y%m%d%H%M%S')
    # print(b)
    #
    # c = CommonUtil.timeformat_convert(timestr1='20200907094345', format1='%Y%m%d%H%M%S', format2='%Y-%m-%d %H:%M:%S')
    # print(c)
    # plate_code = CommonUtil.parse_plate_code('b2e241313233343500000000')
    # print(plate_code)
    # print(CommonUtil.hex_to_etcfee('000026d6', unit='fen'))