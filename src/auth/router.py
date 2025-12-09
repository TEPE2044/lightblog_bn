from fastapi import APIRouter, HTTPException
from src.auth.schemas import SMSFormData, PhoneFormData, AccountFormData
from src.auth.services import send_sms_code_async, is_code_valid
from src.database import db_dependency
from src.utils import phoneRegex

authRouter = APIRouter(prefix="/auth", tags=['登录模块'])


@authRouter.post("/fake-sms-code", summary="伪造短信验证码（测试专用）")
async def fake_sms_code(front: SMSFormData, db: db_dependency):
    try:
        if not front.codeActive:
            return {"status": "400", "msg": "请先获取验证码"}
        result = phoneRegex(front.phone)
        print(result)
        if result:
            return {"status": "200", "msg": "短信发送成功"}
        else:
            return {"status": "400", "msg": "验证码获取失败"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="验证码错误")


@authRouter.post("/fake-login-by-phone", summary="伪造验证码校验（测试专用）")
async def test_code_valid(front: PhoneFormData, db: db_dependency):
    # 伪造验证码校验
    if front.code == "1234":
        return {"status": "200", "msg": "验证码校验成功", "token": "test123"}
    raise HTTPException(status_code=404, detail="验证码错误")


@authRouter.post("/send-sms-code", summary="发送短信验证码")
async def send_sms_code(front: SMSFormData, db: db_dependency):
    try:
        if not front.codeActive:
            return {"status": "400", "msg": "请先获取验证码"}
        result = phoneRegex(front.phone)
        print(result)
        # TODO:最好在短信真正发送成功后再写入冷却记录,使用 Redis,数据暂不录入数据库，防止用户取消注册
        # 都不符合，接入短信服务商API发送短信验证码
        sms_result = await send_sms_code_async(front.phone)
        print(sms_result)
        if result and sms_result:
            return {"status": "200", "msg": "短信发送成功"}
        else:
            return {"status": "400", "msg": "验证码获取失败"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="验证码错误")

'''
@authRouter.post("/login-by-phone", summary="手机号验证码登录")
async def login_by_phone(front: PhoneFormData, db: db_dependency):
    # 检验验证码是否正确(阿里云)
    res = await is_code_valid(args=[front.phone, front.code])
    # TODO:查询数据库中是否有该手机号,没有则注册新用户，
    # TODO:生成token返回前端

    if res:
        return {"status": "200", "msg": "登录成功", "token": "1231231"}
    raise HTTPException(status_code=404, detail="验证码错误")


@authRouter.post("/set-password", summary="设置密码")
async def set_password(front: PhoneFormData, db: db_dependency):
    pass


@authRouter.post("/phoneLogin", summary='手机号登录')
async def phone_login(front: PhoneFormData, db: db_dependency):
    pass


@authRouter.post("/accountLogin", summary='账号密码登录')
async def account_login(front: AccountFormData, db: db_dependency):
    # TODO:直接在数据库检索账号信息，不存在数据的一律不给予通过
    # TODO:校验密码，前端也应该进行加密，密码正确则生成token返回前端
    pass
'''