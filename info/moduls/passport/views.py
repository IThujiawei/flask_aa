#   请求 终止模式 生成响应
from flask import request, abort, make_response, current_app, jsonify, session
# 生成图片验证码&真实值
from info.utils.captcha.captcha import captcha
# redis数据库 MySQL数据库
from info import redis_store, db
# 常量
from info import constants
# 验证码
from . import passport_bp
# 返回状态码
from info.response_code import RET
# 正则, 随机数
import re, random
# 用户关系
from info.models import User
# 发送短信验证码
from info.lib.yuntongxun.sms import CCP
# 检查时间
from datetime import datetime

# **********登陆接口设置*************
# URL：/passport/login参数通过请求体携带: {"mobile": 13800138000, "password": 123456 }
# 请求方式：POST
# 传入参数：JSON格式

"""
1获取数据
    1.mobile: 用户手机号码 , password: 未加密的用户密码    
2校验参数
    1非空判断
    2正则判断号码
3逻辑处理
    1根据前端输入的手机号码判断用户是否存在
    2不存在,提示注册
    3存在,根据用户对象,校验密码
    4密码错误,提示用户或密码错误
    5记录登陆最后登陆时间[将修改操作保存到数据库]
    6使用session记录用户信息

4返回数据
    登陆成功

"""


@passport_bp.route('/login', methods=["POST"])
def login():
    # 1获取数据设置数据格式
    param_data = request.json
    # 1.mobile: 用户手机号码 , password: 未加密的用户密码
    mobile = param_data.get("mobile")
    password = param_data.get("password")

    # 2校验参数
    # 1非空判断
    if not all([mobile, password]):
        current_app.logger.error("参数不足")
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    # 2正则判断号码
    if not re.match(r"1[3-9][0-9]{9}", mobile):
        # 返回错误
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式错误")

    # 3逻辑处理
    # 1根据前端输入的手机号码判断用户是否存在
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询注册用户异常")

    # 2不存在,提示注册
    if not user:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")
    # 3存在,根据用户对象,校验密码
    if user.check_password(password) is False:
        # 4密码错误,提示用户或密码错误
        return jsonify(errno=RET.DATAERR, errmsg="密码密码错误")
    # 5记录登陆最后登陆时间
    # 注意配置数据库字段：SQLALCHEMY_COMMIT_ON_TEARDOWN = True 自动提交数据db.session.commit()
    user.last_login = datetime.now()
    # [将修改操作保存到数据库]

    try:
        db.session.commit()

    except Exception as e:
        current_app.logger.error(e)
        # 数据回滚你
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="提交用户数据库错误")

    # 6使用session记录用户信息
    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    # 4返回数据
    # 登陆成功
    return jsonify(errno=RET.OK, errmsg="登陆成功")


# **********登陆接口结束*************


# ******************注册用户接口 开始*********************
"""实现需求
请求方式 POST
url: /passport/register 
1 获取数据
    1.1 mobile:手机号码， smscode: 用户填写短信验证码， password:未加密的密码
2 校验数据
    2.1 非空判断
    2.2 手机号码格式判断
3 逻辑判断
    3.1 根据手机号码去redis数据库提取正确的短信验证码值
        短信验证码有值：从redis数据库删除 [避免同一个验证码多次验证码] 
        短信验证码没有值：短信验证码过期了 
        3.2 对比`用户填写短信验证码`和正确的短信验证值是否一致
        3.3 不相等：短信验证码填写错误
        3.4 相等：使用User类创建实例对象，给其各个属性赋值
        3.5 将用户对象保存到数据库
        3.6 注册成功表示登录成功，使用session记录用户信息
    4.返回值
        4.1 返回注册成功
4 返回值


"""


# 请求方式 POST
# url: /passport/register
@passport_bp.route("/register", methods=["POST"])
def register():
    # 数据交互方式
    # param_dict: 参数字典
    param_dict = request.json
    # 获取数据
    # 1.1 mobile:手机号码， smscode: 用户填写短信验证码， password:未加密的密码
    mobile = param_dict.get("mobile")
    sms_code = param_dict.get("sms_code")
    password = param_dict.get("password")

    # 2 校验数据
    # 2.1 非空判断
    if not all([mobile, sms_code, password]):
        current_app.logger.error("注册参数不足")
        return jsonify(errno=RET.PARAMERR, errmsg="注册参数不足")

    # 2.2)正则判断 手机格式
    if not re.match(r"1[3578][0-9]{9}", mobile):
        # 返回错误
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式错误")
    # 3 逻辑判断
    # 3.1 根据手机号码去redis数据库提取正确的短信验证码值
    try:
        real_sms_code = redis_store.get("SMS_CODE_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询redis 短信验证码异常")

    # 短信验证码有值：
    if real_sms_code:
        # 从redis数据库删除[避免同一个验证码多次验证码]
        redis_store.delete("SMS_CODE_%s" % mobile)

    # 短信验证码没有值：
    else:
        # 短信验证码过期了
        return jsonify(errno=RET.NODATA, errmsg="短信验证码过期")

    # 3.2 对比`用户填写短信验证码`和正确的短信验证值是否一致
    if sms_code != real_sms_code:
        # 3.3 不相等：短信验证码填写错误
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")

    # 3.4 相等：使用User类创建实例对象，给其各个属性赋值
    user = User()
    # 昵称
    user.nick_name = mobile
    # 手机号码
    user.mobile = mobile

    # TODO:密码加密
    # user.set_password_hash = password
    user.password = password

    # 记录用户最后登陆时间
    # datetime.now() 当前时间
    user.last_login = datetime.now()

    # 3.5 将用户对象保存到数据库
    try:
        # add增加
        db.session.add(user)
        # commit提交
        db.session.commit()
    except Exception as e:
        # 记录异常
        current_app.logger.error(e)
        # 数据库回滚
        db.session.rollback()

        return jsonify(errno=RET.DBERR, errmsg="保存用户异常11111")
    # 3.6 注册成功表示登录成功，使用session记录用户信息
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    # 4.返回值
    # 4.1 返回注册成功
    return jsonify(errno=RET.OK, errmsg="注册成功")


# ******************注册用户接口 结束********************


# """""""""""""""""""""""""""短信验证码接口开始"""""""""""""""""""""""

"""原理

请求方式:"post"
请求url:/passport/sms_code
请求&返回data的格式: Json
思路:
1获取参数.
    1.1)用户账号手机号码, 用户填写真实图片验证码: image_code, 编号UUID:images_code_id

2校验参数.
    2.1)非空判断, mobile,image_code, images_code_id是否为空.
    2.2)正则判断 手机格式

3逻辑处理.
    3.1)根据UUID 取redis数据库图片验证码的真实值.
        3.1.1)redis数据库 图片验证码真实值储在, 将其值从redis数据库删除(防止他人那同一个验证码来验证)
        3.1.2)真实值不存在, 返回前端验证过期.
    3.2)获取用户填写的真实图片验证码值 & redis数据库的真实值进行比较
    3.3)不相等,告诉前端图片验证码错误 4004    

TODO:判断手机号码是否以注册

    3.4)图片验证码相等,生成六位数短信验证码,调用第三方接口发送短信验证码
        3.4.1)发送验证码失败:告知前端
    3.5) 将6位数验证码储存到redis数据库 设置有效时间.

4返回值.

    4.1)返回短信验证码发送成功  OK=0
"""


# 请求url:/passport/sms_code 参数通过请求体携带{mobile:13800138000, images_code:12345}
@passport_bp.route("/sms_code", methods=["POST"])
def send_sms_code():
    # 1获取参数.
    # 1.1)用户账号mobile号码, 用户填写真实图片验证码: image_code, 编号UUID:images_code_id
    param_data = request.json
    print(param_data)

    mobile = param_data.get("mobile")
    image_code = param_data.get("image_code")
    image_code_id = param_data.get("image_code_id")

    # 2校验参数.
    # 2.1)非空判断, mobile,image_code, images_code_id是否为空.
    if not all([mobile, image_code, image_code_id]):
        # 日志记录参数不足
        current_app.logger.error("参数不足")
        # 返回错误信息
        # error_data={"errno":RET.DATAERR, "errmsg": "参数不足"}
        # return jsonify(error_data)
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足1")

    # 2.2)正则判断 手机格式
    if not re.match(r"1[3-9][0-9]{9}", mobile):
        # 返回错误
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式错误")
    # TODO 验证手机号码

    # 3逻辑处理.
    # 3.1)根据UUID 取redis数据库图片验证码的真实值.
    try:
        real_image_code = redis_store.get("Image_Code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        # jsonify: 返回js数据
        return jsonify(errno=RET.DBERR, errmsg="查询redis数据库图片验证码异常")
    # 3.1.1)redis数据库 图片验证码真实值储在, 将其值从redis数据库删除(防止他人那同一个验证码来验证)
    if real_image_code:
        # 将其值从redis数据库删除(防止他人那同一个验证码来验证)
        # delete :删除
        redis_store.delete("Image_Code_%s" % image_code_id)
    # 3.1.2)真实值不存在, 返回前端验证过期.
    else:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码过期")

    # 3.2)获取用户填写的真实图片验证码值 & redis数据库的真实值进行比较
    # image_code:用户填写的图片验证码
    # real_image_code: redis数据库 的真实值
    # lower() 设置成小写
    if image_code.lower() != real_image_code.lower():
        # 不相等的情况下 提示 前端图片验证码错误, 获取4004状态码 并重新生成一个图片验证码
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码输入错误")

    # TODO:判断手机号码是否以注册

    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户异常")

    if user:
        # 注册过的手机号码提示
        return jsonify(errno=RET.DATAERR, errmsg="手机号码以注册")

    # 3.4)图片验证码相等,生成六位数短信验证码,调用第三方接口发送短信验证码
    real_sms_code = random.randint(0, 999999)
    # 不知六位后面补0 000001
    real_sms_code = "%06d" % real_sms_code

    print("短信验证码", real_sms_code)

    # """"""""""""""""第三方发送短信验证码开始""""""""""""""""""""

    # 3.4.2 调用CPP对象的send_template_sms发送短信验证码
    # 参数1：发送到那个手机号码 mobile
    # 参数2：发送短信的内容,有效时间  real_sms_code, 5
    # 参数3： 短信模板id   1

    # try:
    #     result = CCP().send_template_sms(mobile, {real_sms_code, 5}, 1)
    # except Exception as e:
    #     current_app.logger.error(e)
    #
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送短信验证码异常")
    # # 发送失败告诉 前端
    # if result == -1:
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送短信验证码异常")

    # """"""""""""""""""""""第三方发送短信验证码结束""""""""""""""

    # 3.4.4 发送短信验证码成功：使用redis数据库保存正确的短信验证码值
    redis_store.setex("SMS_CODE_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, real_sms_code)

    # 4.1)返回短信验证码发送成功  OK=0
    return jsonify(errno=RET.OK, errmsg="发送成功")

    # """""""""""""""""""""""""""短信验证码结束"""""""""""""""""""""""


# """""""""""""""""""""图片验证码后端接口""""""""""""""""""""""""""
# /passport/image_code?code_id=UUID编号
@passport_bp.route('/image_code')
def get_image_code():
    """生成验证码图片的后端接口"""

    """
    1.获取参数
        1.1 code_id: UUID唯一编码
    2.参数校验
        2.1 code_id非空判断
    3.业务逻辑
        3.1 调用工具类生成验证码图片，验证码真实值
        3.2 使用code_id作为key将验证码真实值存储到redis中，并且设置有效时长
    4.返回数据
        4.1 返回图片数据
    """

    # 1.1 code_id: UUID唯一编码
    code_id = request.args.get("code_id")

    # 2.1 code_id非空判断
    if not code_id:
        return abort(404)

    # 3.1 调用工具类生成验证码图片，验证码真实值
    '''
    image_name: 验证码名称
    real_image_code: 真实验证码值
    image_data: 验证码图片数据
    '''
    image_name, real_image_code, image_data = captcha.generate_captcha()

    # 3.2 使用code_id作为key将验证码真实值存储到redis中，并且设置有效时长，方便下一个接口提取正确的值
    """
    参数1：存储的key :"Image_Code_%s" % code_id
    参数2：有效时长，: constants.IMAGE_CODE_REDIS_EXPIRES
    参数3：redis_store 数据库存储 的真实值: real_image_code
    """
    print("图片验证码", real_image_code)
    redis_store.setex("Image_Code_%s" % code_id, constants.IMAGE_CODE_REDIS_EXPIRES, real_image_code)

    # 4.1 直接返回图片数据，不能兼容所有浏览器
    """make_response:构建响应对象 """
    response = make_response(image_data)

    # 设置响应头中返回的数据格式为：png格式
    response.headers["Content-Type"] = "png/image"
    return response

# """""""""""""""""""""图片验证码后端接口""""""""""""""""""""""""""
