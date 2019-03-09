from ..index import index_bp

# 3使用蓝图装饰视图函数
@index_bp.route('/')
def index():

    return "index"
