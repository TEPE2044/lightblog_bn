from typing import Optional

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import APIRouter, HTTPException, Request, Query, Depends

from src.auth.schemas import SMSFormData, PhoneFormData, AccountFormData
from src.auth.services import send_sms_code_async, is_code_valid, phone_validation, \
    recent, is_user_exists, register_new_user, account_validation, user_login, password_strength_validation, \
    hash_password, store_hashed_password, login_out
from src.database import db_dependency, rd_dependency
from src.user.services import query_user, auth_current_user, auth_phone
from src.auth.services import send_html_mail
from src.utils.jwt_client import create_access_token, create_reks_code, create_all_tokens, create_temp_code

authRouter = APIRouter(prefix="/auth", tags=['登录模块'])
limiter = Limiter(key_func=get_remote_address)


@authRouter.post("/login-by-account", summary="账号登录")
async def login_by_account(front: AccountFormData, db: db_dependency, rd: rd_dependency):
    # 检查账号格式 + 校验是否有账号
    is_account = await account_validation([front.account, front.password])

    # 账号密码是否正确 没有直接返回失败：账号不存在 有账号：密码正确发token 错误返回失败
    if is_account is True:
        isRight = await user_login(front.account, front.password, db)
        if isRight is False:
            raise HTTPException(status_code=400, detail="账号不存在或账号信息错误")
        else:
            tokens = await create_all_tokens(front.account, rd)
            return {"status": "200", "msg": "账号登录成功", "tokens": tokens}
    else:
        raise HTTPException(status_code=400, detail="账号不存在或账号信息错误")


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


# checkout
@authRouter.post("/login-by-phone", summary="手机号验证码登录")
async def login_by_phone(front: PhoneFormData, db: db_dependency, rd: rd_dependency):
    isPhone = await phone_validation(front.phone)
    isRecent = await recent(front.phone, rd)
    # 避免键值对堆积
    await rd.delete(front.phone)
    await rd.setex(front.phone, 300, front.code)
    if isPhone is False:
        raise HTTPException(status_code=400, detail="手机号格式错误")
    if isRecent is True:
        tokens = await create_all_tokens(front.phone, rd)
        # user_info = await query_user(front.phone, db)
        return {"status": "200", "msg": "登录成功", "tokens": tokens}

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
        tokens = await create_all_tokens(front.phone, rd)
        return {"status": "200", "msg": "登录成功", "tokens": tokens}
    else:
        # 注册新用户
        await register_new_user(front.phone, db)
        tokens = await create_all_tokens(front.phone, rd)
        return {"status": "201", "msg": "新用户注册成功，请完善资料", "tokens": tokens}
        # 生成token返回前端


# 新增退出接口，让前端在点击退出登录时里调一次 logout
@authRouter.get("/logout", summary="退出登录")
async def logout(rd: rd_dependency, request: Request):
    # 实现退出登录功能,检索请求中的手机号，然后在redis中找到对应的reks_code进行清除
    is_login_out = await login_out(request, rd)
    print(is_login_out)
    return {"status": "200", "msg": "退出登录成功"}


# 设置密码
@authRouter.post("/set-password-safety", summary="设置账号密码")
@limiter.limit("1/month")  # 想要用limiter，需要显式定义request
async def set_password_safety(psw: str, db: db_dependency, phone: auth_phone, request: Request):
    # 密码至少8位，上限30位
    # 包含大小写字母，数字，特殊字符
    # 检验令牌，并且从令牌中获取手机号
    if phone is False:
        raise HTTPException(status_code=401, detail="登录已失效,请重新登录")

    is_strong = await password_strength_validation(psw)
    if is_strong is False:
        raise HTTPException(status_code=400,
                            detail="密码强度不足，需包含大小写字母、数字、特殊字符，且长度在8-30位之间")
    else:
        try:
            # 对密码进行哈希，加盐
            psw = await hash_password(psw)
            # 存入数据库
            is_stored = await store_hashed_password(phone, psw, db)
            if is_stored is True:
                return {"status": "200", "msg": "密码设置成功"}
        except HTTPException as e:
            print(e)
            raise HTTPException(status_code=500, detail="密码设置失败，请稍后再试")


# 设置邮箱
@authRouter.post("/set-email-safety", summary="设置邮箱")
@limiter.limit("1/month")  # 想要用limiter，需要显式定义request
async def set_email_safety(email: str, rd: rd_dependency, request: Request):
    tc = await create_temp_code(rd, email)
    rlink = f'http://v1.rekindlers.top/api/v1/auth/verify-email?token={tc}'  # 测试专用
    is_send = await send_html_mail(email, rlink)
    if is_send is not True:
        raise HTTPException(status_code=500, detail="发送邮件失败")


@authRouter.post("/reset-pn", summary="邮箱重置手机号")
@limiter.limit("5/month")  # 想要用limiter，需要显式定义request
async def reset_pn(email: str, phone: str, reset_phone: str, rd: rd_dependency):
    # TODO:检验旧手机号是否在库，
    # TODO:检验新手机号是否正规手机号
    #
    tc = await create_temp_code(rd, email)
    # rlink = f'https://dev.rekindlers.top?token={tc}'
    rlink = f'http://localhost:12404/api/v1/auth/verify-email?token={tc}'  # 测试专用
    is_send = await send_html_mail(email, rlink)
    if is_send is not True:
        raise HTTPException(status_code=500, detail="发送邮件失败")


# TODO:重置手机号

# 校验邮箱
# 用途1：设置密码

@authRouter.get("/verify-email", summary="验证邮箱")
async def email_check(rd: rd_dependency, token: str = Query(..., min_length=20, description="邮箱临时令牌")):
    try:
        email = await rd.get(f"temp{token}")
        if email is None:
            raise HTTPException(status_code=404, detail="令牌无效或已过期")
        await rd.delete(f"temp{token}")
        print("邮箱校验成功")
        return {'msg': "邮箱绑定成功"}
    except Exception as e:
        print(e)
        raise HTTPException(400, "流程出错，请联系管理员！")


# TODO:更换手机号
@authRouter.post("/change-phone-safety", summary="换绑手机号")
async def change_phone_safety(phone: str, new_phone: str):
    pass


# TODO:销户
@authRouter.post("/destroy-account", summary="注销账号")
async def destroy_account(phone):
    pass
