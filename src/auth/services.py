import random
from typing import List, Sized, Any, Coroutine

import bcrypt
from sqlalchemy import select, exists, insert, update
from sqlalchemy.exc import IntegrityError

from src.database import db_dependency, rd_dependency
from src.orm.model import User
from src.utils.aliyun_client import create_client
from alibabacloud_dypnsapi20170525.models import SendSmsVerifyCodeRequest, CheckSmsVerifyCodeRequest
from alibabacloud_tea_util.models import RuntimeOptions
import re


# SendSmsVerifyCodeRequest他妈的早就废弃了，示例还在用，气死我了
# 搞半天自摆乌龙

# aliyun-pns:sendSmsVerifyCode
async def send_sms_code_async(phone: str) -> bool:
    client = create_client()
    print(f"发送短信验证码到手机号: {phone}")
    reks_req = SendSmsVerifyCodeRequest(
        phone_number=phone,
        sign_name='速通互联验证平台',
        template_code='100001',
        template_param='{"code":"##code##","min":"5"}',
        auto_retry=1
    )
    runtime = RuntimeOptions()
    try:
        sms_res = await client.send_sms_verify_code_with_options_async(reks_req, runtime)
        bizId = sms_res.body.model
        success = sms_res.body.success
        if not bizId:
            print("验证码发送失败,获取bizId失败")
            return False
        else:
            print(bizId)
            # print(sms_res.body.success, type(sms_res.body.success), success, type(success))
            return bool(success)
    except Exception as e:
        # 此处逻辑需要根据实际情况处理
        print("验证码发送失败", e)
        return False


# aliyun-pns:checkSmsVerifyCode
async def is_code_valid(args: List[str], rd: rd_dependency) -> bool:
    client = create_client()
    check_sms_verify_code_request = CheckSmsVerifyCodeRequest(
        phone_number=args[0],
        verify_code=args[1]
    )
    runtime = RuntimeOptions()
    try:
        res = await client.check_sms_verify_code_with_options_async(check_sms_verify_code_request,
                                                                    runtime)
        success = res.body
        verfiyresult = res.body.model
        print(verfiyresult)
        # bug fix
        await rd.setex(args[0], 300, args[1])
        return bool(success)
    except Exception as e:
        print("验证码校验失败", e)
        return False


async def phone_validation(phone: str) -> bool:
    pattern = re.compile(r"^1[3-9]\d{9}$")
    return bool(re.match(pattern, phone))


async def is_user_exists(phone: str, db: db_dependency) -> bool:
    return await db.scalar(select(exists().where(User.phone == phone)))


async def register_new_user(phone: str, db: db_dependency) -> bool:
    new_user = insert(User).values(phone=phone, username=f"探星使者_{random.randint(10000, 99999)}")
    try:
        await db.execute(new_user)
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False


async def recent(phone: str, rd: rd_dependency) -> bool:
    ok = await rd.exists(phone)
    # test passed
    # print("手机号", type(phone), phone)
    # print("redis", bool(ok))
    return bool(ok)


async def account_validation(args: List[str]) -> bool:
    if args is None or len(args) != 2:
        return False
    account = bool(await phone_validation(args[0]) and args[0] is not None)
    password = bool(args[1] is not None and len(args[1]) >= 6)
    return account and password


async def password_strength_validation(psw: str) -> bool:
    pattern = r'^(?![A-Za-z]+$)(?!\d+$)(?![^A-Za-z0-9]+$)[^\s]{6,30}$'
    return bool(re.match(pattern, psw))


# 注册
async def hash_password(psw: str) -> bytes:
    # 前端在https下，不需要二次hash，直接bcrypt
    return bcrypt.hashpw(psw.encode('utf-8'), bcrypt.gensalt(rounds=12))


# 密码存入数据库
async def store_hashed_password(phone: str, hashed: bytes, db: db_dependency) -> bool:
    try:
        stmt = update(User).where(User.phone == phone).values(hashed_password=hashed.decode("utf-8"))
        await db.execute(stmt)
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False


async def user_login(phone: str, psw: str, db: db_dependency) -> bool:
    # 查询改手机号
    try:
        stmt = select(User).where(User.phone == phone)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        # print(user.hashed_password)
        if user.hashed_password is None:
            return False
        return await check_password(psw, user.hashed_password, db)
    except IntegrityError:
        await db.rollback()
        return False


async def login_out(request, rd: rd_dependency) -> bool:
    header_rcode = request.headers.get("authorization") or ""
    if not header_rcode.lower().startswith("bearer "):
        return False
    rcode = header_rcode[7:]
    return bool(await rd.delete(f"sess:{rcode}"))


# 登录
# 不清楚这个TODO：BUG，加密后究竟是什么类型的
async def check_password(psw: str, hashed: str, db: db_dependency) -> bool:
    # 校对密码
    try:
        return bool(bcrypt.checkpw(psw.encode('utf-8'), hashed.encode('utf-8')))
    except IntegrityError:
        await db.rollback()
        return False
