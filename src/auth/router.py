from fastapi import APIRouter, HTTPException
from src.auth.schemas import SMSFormData, PhoneFormData, AccountFormData
from src.auth.services import send_sms_code_async, is_code_valid, phone_validation, isUserExists, registerNewUser, \
    recent
from src.database import db_dependency, rd_dependency

authRouter = APIRouter(prefix="/auth", tags=['登录模块'])


@authRouter.post("/fake-sms-code", summary="伪造短信验证码（测试专用）")
async def fake_sms_code(front: SMSFormData, db: db_dependency):
    if front.codeActive is False:
        return {"status": "400", "msg": "验证码发送失败"}
    phoneRegex = await phone_validation(front.phone)
    print(phoneRegex)
    if phoneRegex is True:
        # sms
        return {"status": "200", "msg": "验证码发送成功", "code": "1234"}
    else:
        raise HTTPException(status_code=400, detail="验证码发送失败")


@authRouter.post("/fake-login-by-phone", summary="伪造验证码校验（测试专用）")
async def test_code_valid(front: PhoneFormData, db: db_dependency):
    isPhone = await phone_validation(front.phone)
    isCode = front.code == "1234"
    res = isCode and isPhone and bool(front.iaccept)
    # 检查手机号是否正确
    if isPhone is False:
        raise HTTPException(status_code=400, detail="手机号格式错误")
    # 检查用户是否同意协议
    elif front.iaccept is False:
        raise HTTPException(status_code=400, detail="用户未同意协议")
    # 检验验证码是否正确(阿里云)
    elif isCode is False:
        raise HTTPException(status_code=400, detail="验证码检验失败")

    if res is False:
        raise HTTPException(status_code=400, detail="登录失败")
    print(res, "表单数据检验完毕")
    isUser = await isUserExists(front.phone, db)

    if res and isUser is True:
        return {"status": "200", "msg": "验证码校验成功，欢迎回家", "token": "test123"}
    else:
        return {"status": "404", "msg": "这是一个新用户"}


@authRouter.post("/send-sms-code", summary="发送短信验证码")
async def send_sms_code(front: SMSFormData, db: db_dependency):
    try:
        if front.codeActive is False:
            raise HTTPException(status_code=400, detail="验证码发送失败")
        phoneRegex = await phone_validation(front.phone)
        # print(phoneRegex)
        if phoneRegex is True:
            sms_result = await send_sms_code_async(front.phone)
            print(sms_result)
            return {"status": "200", "msg": "验证码发送成功"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="验证码错误")


@authRouter.post("/login-by-phone", summary="手机号验证码登录")
async def login_by_phone(front: PhoneFormData, db: db_dependency, rd: rd_dependency):
    isPhone = await phone_validation(front.phone)
    isRecent = await recent(front.phone, rd)
    if isRecent is True:
        return {"status": "200", "msg": "登录成功", "token": "1231231"}
    if isPhone is False:
        raise HTTPException(status_code=400, detail="手机号格式错误")
    # 检查用户是否同意协议
    elif front.iaccept is False:
        raise HTTPException(status_code=400, detail="用户未同意协议")
    # 检验验证码是否正确(阿里云)
    isCode = await is_code_valid([front.phone, front.code],rd)
    if isCode is False:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    print("表单数据检验完毕")

    # 查询数据库中是否有该手机号,没有则注册新用户，
    isUser = await isUserExists(front.phone, db)
    print(isUser, "用户存在性检查完毕")
    if isUser is True:
        # TODO:生成token返回前端
        return {"status": "200", "msg": "登录成功", "token": "1231231"}
    else:
        # TODO:注册新用户
        await registerNewUser(front.phone, db)

        return {"status": "201", "msg": "新用户注册成功，请完善资料", "token": "1231231"}
        # TODO:生成token返回前端
