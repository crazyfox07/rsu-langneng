#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lxw
@file:vehicle_owe_model.py
@time:2020/11/04
"""


class VehicleOweModel(object):

    def __init__(self, plate_no, plate_color, deduct_amount):
        self.plate_no = plate_no
        self.plate_color = plate_color
        self.deduct_amount = deduct_amount