from typing import List

from fastapi import APIRouter, HTTPException
from src.auth.schemas import SMSFormData, PhoneFormData, AccountFormData
from src.auth.services import send_sms_code_async, is_code_valid, phone_validation, \
    recent, is_user_exists, register_new_user, account_validation, user_login
from src.database import db_dependency, rd_dependency
from src.user.services import query_user
from src.utils.jwt_client import create_access_token, create_reks_code, create_all_tokens

authRouter = APIRouter(prefix="/auth", tags=['登录模块'])


@authRouter.post("/safe-settiings", summary="安全设置")
async def safe_settings():
    # TODO:实现安全设置功能
    # TODO:设置密码，设置邮箱，设置密保问题
    # 后期待开发：安全密钥，直接用于二次验证
    return {"status": "200", "msg": "安全设置成功"}


@authRouter.post("/fake-login-by-account", summary="测试-账号登录")
async def fake_login_by_account(front: AccountFormData, db: db_dependency, rd: rd_dependency):
    # 检查账号格式 + 校验是否有账号
    isAccount = await account_validation([front.account, front.password])

    # 账号密码是否正确 没有直接返回失败：账号不存在 有账号：密码正确发token 错误返回失败
    if isAccount is True:
        isRight = await user_login(front.account, front.password, db)
        if isRight is False:
            raise HTTPException(status_code=400, detail="账号不存在或账号信息错误")
        else:
            tokens = await create_all_tokens(front.account, rd)
            return {"status": "200", "msg": "账号登录成功", "tokens": tokens}
    else:
        raise HTTPException(status_code=400, detail="账号不存在或账号信息错误")


# 测试手机号 17328113179
@authRouter.post("/fake-sms-code", summary="测试-获取短信验证码")
async def fake_sms_code(front: SMSFormData):
    # TODO:后续限制获取验证码的频率
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
@authRouter.post("/fake-login-by-phone", summary="测试-手机号验证码登录")
async def fake_login_by_phone(front: PhoneFormData, db: db_dependency, rd: rd_dependency):
    isPhone = await phone_validation(front.phone)
    isRecent = await recent(front.phone, rd)
    # 避免键值对堆积
    await rd.delete(front.phone)
    await rd.setex(front.phone, 300, front.code)
    if isPhone is False:
        raise HTTPException(status_code=400, detail="手机号格式错误")
    if isRecent is True:
        # 随机串token
        tokens = await create_all_tokens(front.phone, rd)
        return {"status": "200", "msg": "最近登录的", "tokens": tokens}
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
        # payload作为真正的token
        tokens = await create_all_tokens(front.phone, rd)
        return {"status": "200", "msg": "老用户登陆成功", "tokens": tokens}
    else:
        # 注册新用户
        await register_new_user(front.phone, db)
        tokens = await create_all_tokens(front.phone, rd)
        return {"status": "201", "msg": "新用户注册成功，请完善资料", "tokens": tokens,
                "user-status": "new"}
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
        user_info = await query_user(front.phone, db)
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
        user_info = await query_user(front.phone, db)
        return {"status": "200", "msg": "登录成功", "token": token, "data": user_info}
    else:
        # 注册新用户
        await register_new_user(front.phone, db)
        user_info = await query_user(front.phone, db)
        token = await create_access_token(front.phone)
        return {"status": "201", "msg": "新用户注册成功，请完善资料", "token": token,
                "data": user_info}
        # 生成token返回前端


# TODO:新增退出接口
@authRouter.post("/logout", summary="退出登录")
async def logout():
    # TODO:实现退出登录功能
    pass
    # TODO:清除redis对应的reks_code
    pass
    return {"status": "200", "msg": "退出登录成功"}


@authRouter.post("/set-password-safety", summary="设置账号密码")
async def set_password_safety(psw: str):
    # TODO:密码至少8位，上限30位
    if psw is None and 8 > len(psw) > 30:
        raise HTTPException(status_code=400, detail="密码格式错误，密码长度至少6位")
    # TODO:包含大小写字母，数字，特殊字符
    pass
    # TODO:对密码进行哈希，加盐
    pass
    # TODO:存入数据库
    pass
    # TODO:返回成功信息
    return {"status": "200", "msg": "密码设置成功"}
