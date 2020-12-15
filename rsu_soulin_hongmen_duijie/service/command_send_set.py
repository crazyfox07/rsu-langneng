import time
from common.config import CommonConf
from common.utils import CommonUtil


class CommandSendSet(object):
    """
    指令发送集合
    """

    @staticmethod
    def combine_c0(lane_mode='03', wait_time='02', tx_power='0a', pll_channel_id='00', trans_mode='02'):
        """
        组合c0指令， 该指令为初始化指令
        :param lane_mode: 车道工作模式
        :param wait_time: 最小重读时间
        :param tx_power: etc天线功率级数
        :param pll_channel_id: 信道号
        :param trans_mode: 记账模式
        :return:
        """
        # 序列号
        rsctl = CommonUtil.get_rsctl()
        # 指令代码
        cmd_type = 'c0'
        time_stamp = int(time.time())  # 时间戳
        # 记账时间
        unix_time = hex(time_stamp + 8 * 60 * 60)[2:]
        # 当前时间
        current_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time_stamp))
        # 初始化指令
        c0 = ''.join(
            [rsctl, cmd_type, unix_time, current_time, lane_mode, wait_time, tx_power,
             pll_channel_id, trans_mode]).replace('ff', 'fe01').replace('fe', 'fe00')
        c0 = CommonConf.COMMAND_BEGIN_FLAG + c0
        # 异或校验值
        bcc = CommonUtil.bcc_xor(c0)
        c0 = c0 + bcc + CommonConf.COMMAND_END_FLAG
        return c0

    @staticmethod
    def combine_c1(obu_id, obu_div_factor):
        """
        组合c1指令， 该指令为继续交易指令
        :param obu_id: 电子标签mac地址
        :param obu_div_factor: 电子标签一级分散因子，比如"万集万集"的十六进制 'CDF2BCAFCDF2BCAF'
        :return:
        """
        # 序列号
        rsctl = CommonUtil.get_rsctl()
        cmd_type = 'c1'  # 指令代码，此处取值c1
        c1 = ''.join([rsctl, cmd_type, obu_id, obu_div_factor]).replace('ff', 'fe01').replace('fe', 'fe00')
        c1 = CommonConf.COMMAND_BEGIN_FLAG + c1
        # 获取bcc校验值
        bcc = CommonUtil.bcc_xor(c1)
        c1 = c1 + bcc + CommonConf.COMMAND_END_FLAG
        return c1

    @staticmethod
    def combine_c2(obu_id, stop_type='01'):
        """
        组合c2指令，该指令为停止交易指令
        :param obu_id: 电子标签mac地址
        :param stop_type: 1：重新搜索电子标签，不判断电子标签mac地址  2: 重新发送当前帧
        :return:
        """
        # 序列号
        rsctl = CommonUtil.get_rsctl()
        cmd_type = 'c2'  # 指令代码，此处取值c1
        c2 = ''.join([rsctl, cmd_type, obu_id, stop_type]).replace('ff', 'fe01').replace('fe', 'fe00')
        c2 = CommonConf.COMMAND_BEGIN_FLAG + c2
        # 获取bcc校验值
        bcc = CommonUtil.bcc_xor(c2)
        c2 = c2 + bcc + CommonConf.COMMAND_END_FLAG
        return c2

    @staticmethod
    def combine_c4(control_type='00'):
        """
        开关天线指令
        :param control_type: 00-关天线   01-开天线
        :return:
        """
        rsctl = CommonUtil.get_rsctl()
        cmd_type = 'c4'  # 指令代码，此处取值c1
        c4 = ''.join([rsctl, cmd_type, control_type]).replace('ff', 'fe01').replace('fe', 'fe00')
        c4 = CommonConf.COMMAND_BEGIN_FLAG + c4
        # 获取bcc校验值
        bcc = CommonUtil.bcc_xor(c4)
        c4 = c4 + bcc + CommonConf.COMMAND_END_FLAG
        return c4

    @staticmethod
    def combine_c6(obu_id, card_div_factor, reserved, deduct_amount, purchase_time, station):
        """
        组合c6指令，该指令只对ETC天线发送过来的正常b4帧回应有效，消费交易指令，出口消费写过站
        :param obu_id: 电子标签mac地址
        :param card_div_factor: 电子标签一级分散因子，比如"万集万集"的十六进制 'CDF2BCAFCDF2BCAF'
        :param reserved: 保留 四个字节 比如：00000000
        :param consume_money: 扣款额，高字节在前
        :param purchase_time:  YYYYMMDDhhmmss，用此时间去计算TAC码
        :param station: 过站信息（速通卡0012文件或者0019后36/40个字节）
        :return:
        """
        'ffff 86 c6 6a81353e cdf2bcafcdf2bcaf 00000000 00000000 20200826175558 ' \
        '00010001025f46a22e000211223344556677889901020388b2e24131323334350000000000000000 b8 ff'
        # 序列号
        rsctl = CommonUtil.get_rsctl()
        cmd_type = 'c6'  # 指令代码，此处取值c1
        c6 = ''.join([rsctl, cmd_type, obu_id, card_div_factor, reserved, deduct_amount,
                      purchase_time, station]).replace('ff', 'fe01').replace('fe', 'fe00')
        c6 = CommonConf.COMMAND_BEGIN_FLAG + c6
        # 获取bcc校验值
        bcc = CommonUtil.bcc_xor(c6)
        c6 = c6 + bcc + CommonConf.COMMAND_END_FLAG
        return c6
