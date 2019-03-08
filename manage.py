from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# redis数据库
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
# 解决MySQL数据库兼容问题
import pymysql
pymysql.install_as_MySQLdb()

# 调用session类模块
from flask import session
# 调整 flask_session 储存位置工具类
from flask_session import Session

# 调用 数据库块迁移 模块
from flask_migrate import Migrate, MigrateCommand
# 调用 创建数据库管理对象 模块
from flask_script import Manager

# 自定义配置类
class Config(object):
    # 开启DEBUG模式
    DEBUG = True
    # MySQL数据库链接配置
    SQLALCHEMY_DATABASE_URI = "mysql://root1:123456@127.0.0.1:3303/flask_a1"
    # MySQL关闭数据库修改跟踪操作
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis数据库配置 ip
    REDIS_HOST = "127.0.0.1"
    # redis 数据库配置 端口
    REDIS_PORT = 6379

    # ***********设置session配置**************
    # 使用session记录设置加密字符串
    SESSION_KEY = "asdnanasdsdnlka"

    # 将session调整到 redis数据库 保存配置信息
    SESSION_TYPE = "redis"

    # 设置保存到数据库的ip ,端口 , redis数据库对象
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1)

    # 对session_id进行加密处理
    SESSION_USE_SIGNER = True

    # 设置是否永久储存
    SESSION_PERMANENT = True

    # 设置储存有效时间(单位:秒)
    PERMANENT_SESSION_LIFETIME = 86400



# 创建APP对象
app = Flask(__name__)
app.config.from_object(Config)

# 创建MySQL数据库对象
db = SQLAlchemy(app)

# 创建redis 数据库对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

# CSRF 跨站请求伪造
CSRFProtect(app)

#将 flask_session 储存位置从服务器 内存 调到 redis 数据库
Session(app)

# 给项目添加迁移能力
Migrate(app, db)

# 创建数据库管理对象
manager = Manager(app)

# 使用管理对象添加迁移指令
manager.add_command("db", MigrateCommand)



@app.route('/')
def index():
    return "返回值"


if __name__ == '__main__':
    app.run(debug=True)
    # 使用管理对象运行项目
    manager.run()