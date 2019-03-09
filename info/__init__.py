# 调用session类模块
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
# redis数据库
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
# 调整 flask_session 储存位置工具类
from flask_session import Session
# 调用 自定义 config 模块
from config import config_dict


def create_app(config_name):
    # 创建APP对象
    app = Flask(__name__)
    # app.config.from_object(Config)

    # 获取项目配置信息
    config_class = config_dict[config_name]

    app.config.from_object(config_class)

    # 创建MySQL数据库对象
    db = SQLAlchemy(app)

    # 创建redis 数据库对象
    # redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)
    redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    # CSRF 跨站请求伪造
    CSRFProtect(app)

    #将 flask_session 储存位置从服务器 内存 调到 redis 数据库
    Session(app)

    # 返回app对象
    return app

