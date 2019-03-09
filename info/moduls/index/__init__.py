# 导入蓝图类
from flask import Blueprint

"""
1导入蓝图类
2创建蓝图对象
3使用蓝图对象装饰视图函数
4注册蓝图对象

"""

# 创建蓝图类
index_bp = Blueprint("index", __name__)

from .views import *