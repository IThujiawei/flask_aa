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

# 调用日志模块
import logging
# 日志记录器
from logging.handlers import RotatingFileHandler


# 当app对象为空的情况，并没有真正做数据库的初始化操作
db = SQLAlchemy()

# redis数据库对象  # 声明数据类型
redis_store = None  #type: StrictRedis


    # 创建日志信息
# config_class配置类
def write_log(config_class):
    # 记录日志信息

    # 设置日志的记录等级
    logging.basicConfig(level=config_class.LOG_LEVEL)  # 调试debug级

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小100M、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)

    # 创建日志记录的格式：               日志等级      输入日志信息的文件名 行数   日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')

    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)

    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


    # 创建APP对象
def create_app(config_name):

    app = Flask(__name__)
    # app.config.from_object(Config)

    # 获取项目配置信息
    config_class = config_dict[config_name]

    app.config.from_object(config_class)

    # 记录日志
    write_log(config_class)

    # 当app存在的情况，才做真实的数据库初始化操作
    db.init_app(app)

    # 创建redis 数据库对象
    # redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

    # 懒加载
    global redis_store
    redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    # CSRF 跨站请求伪造
    # CSRFProtect(app)

    #将 flask_session 储存位置从服务器 内存 调到 redis 数据库
    Session(app)   # 这是一个工具类

    # 4注册首页蓝图模块
    # 延迟导包,解决循环导包问题
    from info.moduls.index import index_bp
    app.register_blueprint(index_bp)

    # 注册图片验证码蓝图模块
    from info.moduls.passport import passport_bp
    app.register_blueprint(passport_bp)


    # 返回app对象
    return app

