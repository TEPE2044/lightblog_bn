from fastapi import APIRouter, HTTPException
from src.auth.schemas import SMSFormData, PhoneFormData, AccountFormData
from src.auth.services import send_sms_code_async, is_code_valid, phone_validation, \
    recent, is_user_exists, register_new_user, account_validation
from src.database import db_dependency, rd_dependency
from src.user.service import query_user_basic
from src.utils.jwt_client import create_access_token, create_test_token

authRouter = APIRouter(prefix="/auth", tags=['登录模块'])


@authRouter.post("/fake-login-by-account", summary="伪造账号登录（测试专用）")
async def fake_login_by_account(front: AccountFormData, db: db_dependency):
    return {'token': '12341', 'status': 200, 'msg': '登录成功'}


# 测试手机号 17328113179
@authRouter.post("/fake-sms-code", summary="伪造短信验证码（测试专用）")
async def fake_sms_code(front: SMSFormData):
    try:
        if front.codeActive is False:
            raise HTTPException(status_code=400, detail="验证码发送失败")
        phoneRegex = await phone_validation(front.phone)
        # print(phoneRegex)
        if phoneRegex is True:
            return {"status": "200", "msg": "验证码发送成功"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="验证码错误")


# 测试手机号 17328113179
@authRouter.post("/fake-login-by-phone", summary="伪造验证码校验（测试专用）")
async def test_code_valid(front: PhoneFormData, db: db_dependency, rd: rd_dependency):
    isPhone = await phone_validation(front.phone)
    isRecent = await recent(front.phone, rd)
    await rd.setex(front.phone, 300, front.code)
    if isPhone is False:
        raise HTTPException(status_code=400, detail="手机号格式错误")
    if isRecent is True:
        token = await create_test_token(front.phone)
        user_info = await query_user_basic(front.phone, db)
        return {"status": "200", "msg": "最近登录的", "token": token, "userinfo": user_info}
    # 检查用户是否同意协议
    elif front.iaccept is False:
        raise HTTPException(status_code=400, detail="用户未同意协议")
    # 检验验证码是否正确(阿里云)
    isCode = front.code == "1234"
    if isCode is False:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    print(isCode)

    # 查询数据库中是否有该手机号,没有则注册新用户，
    isUser = await is_user_exists(front.phone, db)
    print(isUser, "用户存在性检查完毕")
    if isUser is True:
        # 生成token返回前端
        token = await create_test_token(front.phone)
        user_info = await query_user_basic(front.phone, db)
        return {"status": "200", "msg": "老用户", "token": token, "data": user_info}
    else:
        # 注册新用户
        await register_new_user(front.phone, db)
        user_info = await query_user_basic(front.phone, db)
        token = await create_test_token(front.phone)
        return {"status": "201", "msg": "新用户注册成功，请完善资料", "token": token,
                "data": user_info}
        # 生成token返回前端


@authRouter.post("/send-sms-code", summary="发送短信验证码")
async def send_sms_code(front: SMSFormData):
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
        token = await create_access_token(front.phone)
        user_info = await query_user_basic(front.phone, db)
        return {"status": "200", "msg": "登录成功", "token": token, "userinfo": user_info}
    if isPhone is False:
        raise HTTPException(status_code=400, detail="手机号格式错误")
    # 检查用户是否同意协议
    elif front.iaccept is False:
        raise HTTPException(status_code=400, detail="用户未同意协议")
    # 检验验证码是否正确(阿里云)
    isCode = await is_code_valid([front.phone, front.code], rd)
    if isCode is False:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    print("表单数据检验完毕")

    # 查询数据库中是否有该手机号,没有则注册新用户，
    isUser = await is_user_exists(front.phone, db)
    print(isUser, "用户存在性检查完毕")
    if isUser is True:
        # 生成token返回前端
        token = await create_access_token(front.phone)
        user_info = await query_user_basic(front.phone, db)
        return {"status": "200", "msg": "登录成功", "token": token, "data": user_info}
    else:
        # 注册新用户
        await register_new_user(front.phone, db)
        user_info = await query_user_basic(front.phone, db)
        token = await create_access_token(front.phone)
        return {"status": "201", "msg": "新用户注册成功，请完善资料", "token": token,
                "data": user_info}
        # 生成token返回前端
