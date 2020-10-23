# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: db_migrate.py
@time: 2020/9/3 17:55
"""
from model.db_orm import init_db

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    # 删除数据库的所有表
    # delete_table_all()