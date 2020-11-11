# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: etc_api.py
@time: 2020/9/2 15:40
"""
from fastapi import APIRouter


etc_router = APIRouter()


class ETCApi(object):

    @staticmethod
    @etc_router.get('/route1')
    def route1():
        print('route1')
        return dict(data='route1')

    @staticmethod
    @etc_router.get('/route2')
    def route2():
        print('route2')
        return dict(data='route2')

