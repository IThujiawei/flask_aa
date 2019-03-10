from ..index import index_bp
from info import redis_store
# 3使用蓝图装饰视图函数
@index_bp.route('/')
def index():

    redis_store.setex("name", "laowang")

    return "index"
