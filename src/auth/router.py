import json

from fastapi import APIRouter, HTTPException, Request, Query, Body
from sqlalchemy import update, func
from fastapi.responses import HTMLResponse

from src.auth import ans
from src.auth.schemas import SMSFormData, PhoneFormData, AccountFormData, ResetData
from src.auth.services import send_sms_code_async, is_code_valid, phone_validation, \
    recent, is_user_exists, register_new_user, account_validation, user_login, password_strength_validation, \
    hash_password, store_hashed_password, login_out, set_email, check_all_phones, confirm_reset_phone, change_phone, \
    login_core
from src.database import db_dependency, rd_dependency
from src.deps import limiter
from src.orm.model import User
from src.user.services import auth_phone, query_user_rid
from src.auth.services import send_html_mail
from src.utils.Rback import rback

from src.utils.jwt_client import create_all_tokens, create_temp_code

authRouter = APIRouter(prefix="/auth", tags=['登录模块'])


@authRouter.post("/login-by-account", summary="账号登录")
async def login_by_account(front: AccountFormData, db: db_dependency, rd: rd_dependency):
    # 检查账号格式 + 校验是否有账号
    is_account = await account_validation([front.account, front.password])

    # 账号密码是否正确 没有直接返回失败：账号不存在 有账号：密码正确发token 错误返回失败
    if is_account is True:
        isRight = await login_core(front, db)
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
        print(e)
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
        return {"status": "201", "msg": "新用户注册成功，请完善资料", "tokens": tokens, "sign": "new"}
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
async def set_password_safety(db: db_dependency, phone: auth_phone, request: Request, psw: str = Body(..., embed=True)):
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
@limiter.limit("5/month")  # 想要用limiter，需要显式定义request
async def set_email_safety(rd: rd_dependency, db: db_dependency, request: Request, phone: auth_phone,
                           email: str = Body(..., embed=True)):
    if phone is False:
        raise HTTPException(status_code=401, detail="登录已失效,请重新登录")
    reks_id = await query_user_rid(phone, db)
    tc = await create_temp_code(rd, email)
    print("---1")
    # rlink = f'https://v1.rekindlers.top/api/v1/auth/verify-email?token={tc}&reks_id={reks_id}'
    rlink = f'http://localhost:12404/api/v1/auth/verify-email?token={tc}&reks_id={reks_id}'  # 测试专用
    is_send = await send_html_mail(email, rlink)
    if is_send is True:
        return {"status": 200, "msg": "验证邮件发送成功"}
    else:
        raise HTTPException(status_code=500, detail="发送邮件失败")


# 校验邮箱
# 用途1：设置密码

@authRouter.get("/verify-email", summary="验证邮箱")
async def email_check(rd: rd_dependency, db: db_dependency,
                      token: str = Query(..., min_length=20, description="邮箱临时令牌")
                      , reks_id: int = Query(..., description="用户id")):
    try:
        email = await rd.get(f"temp{token}")
        if email is None:
            raise HTTPException(status_code=404, detail="令牌无效或已过期")
        is_email_set = await set_email(email, reks_id, db)
        if is_email_set is True:
            await rd.delete(f"temp{token}")
            print("邮箱校验成功")
            return HTMLResponse(content=ans, status_code=200)
        else:
            raise HTTPException(status_code=400, detail="邮箱设置失败！")
    except Exception as e:
        print(e)
        raise HTTPException(400, "流程出错，请联系管理员！")


@authRouter.get("/verify-email/reset", summary="重置手机号")
async def reset_phone(rd: rd_dependency, db: db_dependency,
                      token: str = Query(..., min_length=20, description="邮箱临时令牌")):
    try:
        raw = await rd.get(f"temp:reset{token}")
        # print(raw)
        if not raw:
            raise HTTPException(status_code=404, detail="手机号重置失败")
        data = json.loads(raw)
        is_reset = await confirm_reset_phone(data, db)
        if is_reset is True:
            await rd.delete(f"temp:reset{token}")
            return {"status": 200, "msg": "手机号重置成功"}
        else:
            raise HTTPException(status_code=400, detail="手机号重置失败")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="手机号重置失败")


# 找回手机号
# 本站目前仅支持通过邮箱重置手机号
# 参数需要：旧手机号（检查格式，查询 if no->end if yes->邮箱），邮箱（检查格式，查询 if no->end if yes->发送邮件），新手机号（检查格式，查询if ）
# 流程1：没设置邮箱->end
# 流程2：有设置邮箱->向邮箱发送一封HTML邮件->token校验成功->重置成功
@authRouter.post("/find-back", summary="手机号已无法使用")
async def find_back(data: ResetData, db: db_dependency, rd: rd_dependency):
    isPhone = await phone_validation(data.new_phone) and await phone_validation(data.old_phone)
    if isPhone is False:
        raise HTTPException(400, "手机号无效或不存在")
    # 检查手机号
    isExists = await check_all_phones(data, db)
    if isExists is False:
        raise HTTPException(400, "用户未设置邮箱、账号不存在或手机号已被使用")
    # 生成临时token
    tc = await create_temp_code(rd, data.email, data)
    try:

        # rlink = f'https://v1.rekindlers.top/api/v1/auth/verify-email?token={tc}'
        rlink = f'http://localhost:12404/api/v1/auth/verify-email/reset?token={tc}'  # 测试专用
        is_send = await send_html_mail(data.email, rlink)

        if is_send is True:
            return {"status": 200, "msg": "验证邮件发送成功"}
        else:
            await rd.delete(f"temp:reset{tc}", data.email)
            raise HTTPException(status_code=500, detail="发送邮件失败")
    except Exception as e:
        print(e)
        if tc:
            await rd.delete(f"temp:reset{tc}", data.email)


# 更换手机号
# 要用户重新登录
@authRouter.post("/change-phone-safety", summary="换绑手机号")
@limiter.limit("1/month")
async def change_phone_safety(phone: auth_phone, new_phone: str, db: db_dependency, rd: rd_dependency,
                              request: Request):
    if phone is False:
        raise HTTPException(401, "登录已失效,请重新登录")
    is_change = await change_phone(new_phone, phone, db)
    if is_change is True:
        try:
            await login_out(request, rd)
        except Exception as e:
            print(e)
        return rback(200, "更改手机号成功，请重新登录")
    else:
        raise HTTPException(400, "修改手机号失败")


# 待测试
@authRouter.post("/destroy-account", summary="注销账号")
async def destroy_account(phone: auth_phone, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "登录已失效,请重新登录")
    stmt = update(User).values(status='deleted', deleted_at=func.now()).where(User.phone == phone)
    try:
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, f"注销失败:{e}")


@authRouter.post("/login-by-account-admin", summary="管理员账号登录")
async def login_by_account_admin(front: AccountFormData, db: db_dependency, rd: rd_dependency):
    # 检查账号格式 + 校验是否有账号
    is_account = await account_validation([front.account, front.password])

    # 账号密码是否正确 没有直接返回失败：账号不存在 有账号：密码正确发token 错误返回失败
    if is_account is True:
        isRight = await login_core(front, db)
        if isRight is False:
            raise HTTPException(status_code=400, detail="账号不存在或账号信息错误")
        else:
            tokens = await create_all_tokens(front.account, rd)
            return {"status": "200", "msg": "账号登录成功", "tokens": tokens}
    else:
        raise HTTPException(status_code=400, detail="账号不存在或账号信息错误")