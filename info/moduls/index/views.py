from info.models import User
from info.moduls.index import index_bp
from info import redis_store
from flask import render_template, current_app, session


# from . import index_bp


# 3.使用蓝图对象装饰视图函数
@index_bp.route('/')
def index():
    # ----------------------1.查询用户基本信息展示----------------------

    # 1.根据session获取用户user_id
    user_id = session.get("user_id")

    user = None
    # 先定义，再使用 否则：local variable 'user_dict' referenced before assignment
    user_dict = None
    if user_id:
        # 2.根据user_id查询用户对象
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return "查询用户对象异常"

        # 3.将用户对象转换成字典
        """
        if user:
            user_dict = user.to_dict()
        """
        user_dict = user.to_dict() if user else None

    # 返回模板的同时将查询到的数据一并返回
    """
        数据格式：
        data = {
            "user_info": {
                            "id": self.id,
                            "nick_name": self.nick_name,
                            }
        }

        使用： data.user_info.nick_name

    """
    # 组织返回数据
    data = {
        "user_info": user_dict
    }

    return render_template("news/index.html", data=data)


# 网站自动调用通过/favicon.ico路由请求一张网站图标
@index_bp.route('/favicon.ico')
def get_favicon():
    """

    Function used internally to send static files from the static
        folder to the browser
    内部使用send_static_file方法将静态文件夹中的图片数据发送到浏览器
    """
    # 找到网站图片的静态资源并返回
    return current_app.send_static_file("news/favicon.ico")