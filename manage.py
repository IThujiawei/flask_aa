
# 解决MySQL数据库兼容问题
import pymysql

# 调用 创建数据库管理对象 模块
from flask_script import Manager
# 调用 数据库块迁移 模块
from flask_migrate import Migrate, MigrateCommand
# 导入app对象
from info import create_app, db, redis_store

pymysql.install_as_MySQLdb()

from flask import current_app

import logging


# 调用工厂方法创建app对象
app = create_app("development")

# 给项目添加迁移能力
Migrate(app, db)

# 创建数据库管理对象
manager = Manager(app)

# 使用管理对象添加迁移指令
manager.add_command("db", MigrateCommand)



# @app.route('/')
# def index():
#
#     logging.debug("This is a debug log.")
#     logging.info("This is a info log.")
#     logging.warning("This is a warning log.")
#     logging.error("This is a error log.")
#     logging.critical("This is a critical log.")
#
#     # flask中也封装了loging模块
#     current_app.logger.debug("flask ---debug")
#
#
#     return "返回值"


if __name__ == '__main__':
    # app.run(debug=True)
    # 使用管理对象运行项目
    manager.run()