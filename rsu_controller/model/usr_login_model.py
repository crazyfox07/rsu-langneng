#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:usr_login_model.py
@time:2021/03/01
"""
from pydantic import BaseModel


class UsrLoginModel(BaseModel):
    username: str
    password: str