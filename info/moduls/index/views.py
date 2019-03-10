from ..index import index_bp
from info import redis_store
# 导入视图模块
from flask import render_template, current_app

# 3使用蓝图装饰视图函数
@index_bp.route('/')
def index():

    redis_store.setex("name",10, "laowang")
    # 指明 index.html 路径 注意js 路径
    return render_template("news/index.html")



# 返回网站图标
@index_bp.route("/favicon.ico")
def favicon():

    # 找到网站图片的静态资源返回浏览器
    # current_app 获取当前 app 名称的
    return current_app.send_static_file("news/favicon.ico")
