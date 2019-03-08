from redis import StrictRedis


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

    # 调用开发模式
class DevelopmentConfig(Config):
    # 开启开发模式
    DEBUG = True


    # 调用上线模式
class ProductionConfig(Config):
    # 关闭调试模式
    DEBUG = False



# 提供一个接口给外界使用
config_dict = {
    "Development" : DevelopmentConfig,
    "Production" :ProductionConfig

}
