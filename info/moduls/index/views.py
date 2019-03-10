from ..index import index_bp
from info import redis_store
# 导入视图模块
from flask import render_template

# 3使用蓝图装饰视图函数
@index_bp.route('/')
def index():

    redis_store.setex("name",10, "laowang")
    # 指明 index.html 路径 注意js 路径
    return render_template("news/index.html")
