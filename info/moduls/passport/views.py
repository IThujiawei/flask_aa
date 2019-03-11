from flask import request, abort,make_response
from info.utils.captcha.captcha import captcha
from info import redis_store
from info import constants
from . import passport_bp


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
    #
    # 参数1：存储的key :"Iamge_Code_%s" % code_id
    # 参数2：有效时长，: constants.IMAGE_CODE_REDIS_EXPIRES
    # 参数3：存储的真实值: real_image_code
    redis_store.setex("Iamge_Code_%s" % code_id, constants.IMAGE_CODE_REDIS_EXPIRES ,real_image_code)

    # 4.1 直接返回图片数据，不能兼容所有浏览器

    # 构建响应对象
    response = make_response(image_data)
    # 设置响应头中返回的数据格式为：png格式
    response.headers["Content-Type"] = "png/image"
    return response


