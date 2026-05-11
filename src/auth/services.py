import random
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from typing import List

import bcrypt
from sqlalchemy import select, exists, insert, update
from sqlalchemy.exc import IntegrityError

from src.auth.schemas import ResetData, AccountFormData
from src.config import settings
from src.database import db_dependency, rd_dependency
from src.orm.model import User, UserSettings
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
    print("-------")
    return await db.scalar(select(exists().where(User.phone == phone)))


async def register_new_user(phone: str, db: db_dependency) -> bool:
    new_user = (
        insert(User)
        .values(phone=phone, username=f"探星使者_{random.randint(10000, 99999)}")
        .returning(User.reks_id)
    )
    try:
        print("-------")
        res = await db.execute(new_user)
        reks_id = res.scalar_one_or_none()
        if reks_id is None:
            await db.rollback()
            return False

        await db.execute(insert(UserSettings).values(user_id=reks_id))
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False


async def recent(phone: str, rd: rd_dependency) -> bool:
    ok = await rd.exists(f"timecode:{phone}")
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


async def login_core(args: AccountFormData, db: db_dependency):
    try:
        stmt = select(User.type).where(User.phone == args.phone)
        is_admin = (await db.execute(stmt)).scalar_one_or_none()
        if is_admin == 'admin' or is_admin == 'supre':
            await admin_login(args.account, args.password, db)
        else:
            await user_login(args.account, args.password, db)
    except Exception as e:
        print(e)
        await db.rollback()


# 管理员只能登管理系统，用户只能登录客户端
async def admin_login(phone: str, psw: str, db: db_dependency) -> bool:
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
    return bool(await rd.delete(f"user:sess:{rcode}"))


# 登录
# 不清楚这个TODO：BUG，加密后究竟是什么类型的
async def check_password(psw: str, hashed: str, db: db_dependency) -> bool:
    # 校对密码
    try:
        return bool(bcrypt.checkpw(psw.encode('utf-8'), hashed.encode('utf-8')))
    except IntegrityError:
        await db.rollback()
        return False


# 发送HTML邮件
# bug:链接无法带入
async def send_html_mail(target: str, rlink: str) -> bool:
    html_content = f"""
    <!doctype html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8" />
        <title>ReKindlers验证码</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body style="margin: 0; padding: 0; background-color: #f5f5f5">
        <table
          role="presentation"
          cellspacing="0"
          cellpadding="0"
          border="0"
          width="100%"
        >
          <tr>
            <td style="padding: 40px 0">
              <!--[if mso]>
              <table role="presentation" align="center" cellpadding="0" cellspacing="0" width="600">
              <tr><td>
              <![endif]-->
              <table
                role="presentation"
                cellspacing="0"
                cellpadding="0"
                border="0"
                width="100%"
                style="
                  max-width: 600px;
                  margin: 0 auto;
                  background-color: #ffffff;
                  border-radius: 6px;
                "
              >
                <tr>
                  <td
                    style="
                      padding: 80px 80px;
                      font-family: Arial, Helvetica, sans-serif;
                      font-size: 16px;
                      line-height: 24px;
                      color: #333333;
                    "
                  >
                    <h2
                      style="
                        margin: 0 0 15px;
                        font-size: 22px;
                        color: rgb(114, 23, 23);
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                      "
                    >
                      ReKindlers 若坎达斯
                    </h2>
                    <p style="color: #999; font-size: 16px">
                      欢迎来到邮箱校验环节,点击下方按钮即可完成邮箱验证。
                    </p>
                    <p style="color: #999; font-size: 14px">
                      本次验证将在10分钟后自动关闭
                    </p>
                    <!-- 按钮区 -->
                    <table
                      role="presentation"
                      cellspacing="0"
                      cellpadding="0"
                      border="0"
                      align="center"
                      style="margin: 30px auto"
                    >
                      <tr>
                        <td style="border-radius: 4px; background-color: #b22223">
                          <a
                            href="{rlink}"
                            target="_blank"
                            style="
                              display: block;
                              padding: 12px 30px;
                              font-size: 16px;
                              font-weight: bold;
                              color: #ffffff;
                              text-decoration: none;
                              border-radius: 4px;
                            "
                            >开始验证</a
                          >
                        </td>
                      </tr>
                    </table>
                    <p style="font-size: 12px; color: #999">
                      如果按钮无法点击，请复制链接到浏览器：<br />{rlink}
                    </p>
                  </td>

                </tr>

              </table>
              <!--[if mso]>
              </td></tr></table>
              <![endif]-->
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    message = MIMEText(html_content, 'html', 'utf-8')
    message['From'] = Header(settings.em_sender)
    message['To'] = Header(target)
    message['Subject'] = Header('一封来自ReKindlers的信')

    try:
        with smtplib.SMTP_SSL('smtp.163.com', 465) as smtp:
            smtp.login(settings.em_sender, settings.em_password)
            smtp.sendmail(settings.em_sender, target, message.as_string())
        print(f"HTML 验证邮件已发送至 {target}")
        return True
    except smtplib.SMTPException as e:
        print("发送失败：", e)
        return False


async def set_email(email: str, reks_id: int, db: db_dependency) -> bool:
    stmt = update(User).values(email=email).where(User.reks_id == reks_id)
    try:
        res = await db.execute(stmt)
        if res.rowcount == 0:
            await db.rollback()
            return False

        await db.commit()
        return True
    except Exception as e:
        print(e)
        await db.rollback()
        return False


async def confirm_reset_phone(data, db: db_dependency) -> bool:
    print(data["old_phone"])
    stmt = update(User).where(User.phone == data["old_phone"], User.email == data["email"]).values(
        phone=data["new_phone"])
    try:
        res = await db.execute(stmt)
        await db.commit()
        print(res.rowcount)
        if res.rowcount > 0:
            return True
        return False
    except Exception as e:
        await db.rollback()
        print(e)
        return False


async def check_all_phones(args: ResetData, db: db_dependency) -> bool:
    # 检查旧邮箱
    stmt = select(User).where(User.phone == args.old_phone, User.email == args.email)
    new_stmt = select(User).where(User.phone == args.new_phone)
    try:
        # 确定有这个账号，有就True，没有就False
        res = (await db.execute(stmt)).scalar_one_or_none()
        if res is None:
            return False
        # 确定手机号是不是注册过了，是就False，没用过才是True
        res = (await db.execute(new_stmt)).scalar_one_or_none()
        if res is None:
            return True
        return False
    except Exception as e:
        print(e)
        return False


# 修改手机号
async def change_phone(new_phone: str, phone: str, db: db_dependency) -> bool:
    # 检测是否为正规手机号
    is_phone = phone_validation(new_phone) and phone_validation(phone)
    if is_phone is False:
        return False
    stmt = update(User).where(User.phone == phone).values(phone=new_phone)
    try:
        is_change = await db.execute(stmt)
        await db.commit()
        return is_change.rowcount > 0
    except Exception as e:
        print(e)
        await db.rollback()
        return False
