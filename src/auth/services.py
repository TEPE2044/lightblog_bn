import asyncio
import random
from typing import List

from sqlalchemy import select, exists, insert
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
            # 存redis去，过期时间5分钟
            # print(sms_res)
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
        res = await client.check_sms_verify_code_with_options_async(check_sms_verify_code_request, runtime)
        success = res.body
        verfiyresult = res.body.model
        print(verfiyresult)
        # 将手机号、验证码存Redis，设置过期时间5分钟
        # bug fix
        await rd.setex(args[0], 300, args[1])
        return bool(success)
    except Exception as e:
        print("验证码校验失败", e)
        return False


async def phone_validation(phone: str) -> bool:
    pattern = re.compile(r"^1[3-9]\d{9}$")
    return bool(re.match(pattern, phone))


# .is_()  是 SQLAlchemy 用来生成 SQL 的  IS  操作符 的方法
async def isUserExists(phone: str, db: db_dependency) -> bool:
    isExist = select(exists().where(User.phone == phone))
    result = await db.execute(isExist)
    return result.scalars()


async def registerNewUser(phone: str, db: db_dependency) -> bool:
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
