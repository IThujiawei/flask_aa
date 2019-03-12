#   请求 终止模式 生成响应
from flask import request, abort, make_response, current_app, jsonify
# 生成图片验证码&真实值
from info.utils.captcha.captcha import captcha
# redis数据库
from info import redis_store
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

# """""""""""""""""""""""""""短信验证码接口开始"""""""""""""""""""""""

"""
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


# 参数通过请求体携带{mobile:13800138000, images_code:12345}
@passport_bp.route("/sms_code", methods=["POST"])
def send_sms_code():
    # 1获取参数.
    # 1.1)用户账号mobile号码, 用户填写真实图片验证码: image_code, 编号UUID:images_code_id
    param_data = request.json
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
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

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

    # 3.4.2 调用CPP对象的send_template_sms发送短信验证码

    # 参数1：发送到那个手机号码 mobile
    # 参数2：发送短信的内容,有效时间  real_sms_code, 5
    # 参数3： 短信模板id   1
    try:
        result = CCP().send_template_sms(mobile, {real_sms_code, 5}, 1)
    except Exception as e:
        current_app.logger.error(e)

        return jsonify(errno=RET.THIRDERR, errmsg="发送短信验证码异常")
    # 发送失败告诉 前端
    if result == -1:
        return jsonify(errno=RET.THIRDERR, errmsg="发送短信验证码异常")

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
    redis_store.setex("Image_Code_%s" % code_id, constants.IMAGE_CODE_REDIS_EXPIRES, real_image_code)

    # 4.1 直接返回图片数据，不能兼容所有浏览器
    """make_response:构建响应对象 """
    response = make_response(image_data)

    # 设置响应头中返回的数据格式为：png格式
    response.headers["Content-Type"] = "png/image"
    return response

# """""""""""""""""""""图片验证码后端接口""""""""""""""""""""""""""
