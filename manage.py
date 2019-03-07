from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# redis数据库
from redis import StrictRedis
# 解决MySQL数据库兼容问题
import pymysql
pymysql.install_as_MySQLdb()

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

# 创建APP对象
app = Flask(__name__)
app.config.from_object(Config)

# 创建MySQL数据库对象
db = SQLAlchemy(app)

# 创建redis 数据库对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

@app.route('/')
def index():
    return "返回值"


if __name__ == '__main__':
    app.run(debug=True)