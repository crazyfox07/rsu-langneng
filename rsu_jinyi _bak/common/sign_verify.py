# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: sign_verify.py
@time: 2020/9/7 16:12
"""
from Crypto import Hash
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import base64

from common.config import CommonConf


class XlapiSignature(object):
    """
    SHA256WithRSA 工具类
    """
    @staticmethod
    def format_private_key(private_key):
        """
        对私进行格式化，缺少"-----BEGIN RSA PRIVATE KEY-----"和"-----END RSA PRIVATE KEY-----"部分需要加上
        :param private_key: 私钥
        :return: pem私钥字符串
        :rtype: str
        """
        pem_begin = '-----BEGIN RSA PRIVATE KEY-----\n'
        pem_end = '\n-----END RSA PRIVATE KEY-----'
        if not private_key.startswith(pem_begin):
            private_key = pem_begin + private_key
        if not private_key.endswith(pem_end):
            private_key = private_key + pem_end
        return private_key

    @staticmethod
    def to_sign_with_private_key(text, private_key):
        """
        用私钥签名
        :param private_key: 私钥
        :return:
        """
        private_key_format = XlapiSignature.format_private_key(private_key)
        content = base64.b64encode(text.encode('utf8'))
        # 私钥签名
        signer_pri_obj = PKCS1_v1_5.new(RSA.importKey(private_key_format))
        rand_hash = Hash.SHA256.new()
        rand_hash.update(content)
        signature = signer_pri_obj.sign(rand_hash)
        auth_signature = base64.b64encode(signature)

        return auth_signature


if __name__ == '__main__':
    private_key = CommonConf.ETC_CONF_DICT['thirdApi']['private_key']
    print(private_key)
    private_key_format = XlapiSignature.format_private_key(private_key)
    print(private_key_format)
    s = XlapiSignature.to_sign_with_private_key('hello', private_key=private_key)
    print(s)