''' new method
isPhone = await phone_validation(front.phone)
isRecent = await recent(front.phone, rd)
await rd.setex(front.phone, 300, front.code)

if isRecent is True:
    token = await create_test_token(front.phone)
    user_info = await query_user_basic(front.phone, db)
    return {"status": "200", "msg": "最近登录的", "token": token, "userinfo": user_info}

checks = [
    (not isPhone, HTTPException(status_code=400, detail="手机号格式错误")),
    (front.iaccept is False, HTTPException(status_code=400, detail="用户未同意协议")),
    (front.code != "1234", HTTPException(status_code=400, detail="验证码无效或已过期")),
]

for condition, exception in checks:
    if condition:
        raise exception

print(front.code == "1234")
'''