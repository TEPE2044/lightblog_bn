import asyncio
import random
from src.utils.aliyun_client import create_client
from alibabacloud_dypnsapi20170525.models import SendSmsVerifyCodeRequest
from alibabacloud_tea_util.models import RuntimeOptions


# SendSmsVerifyCodeRequest他妈的早就废弃了，示例还在用，气死我了
# 搞半天自摆乌龙

async def send_sms_code_async(phone: str) -> bool:
    client = create_client()
    code = ''.join(random.choices('0123456789', k=6))
    print(f"发送短信验证码: {code} 到手机号: {phone}")
    reks_req = SendSmsVerifyCodeRequest(
        phone_number=phone,
        sign_name='速通互联验证码',
        template_code='100001',
        template_param='{"code":"##code##","min":"5"}',
        auto_retry=1
    )
    runtime = RuntimeOptions()
    try:
        sms_res = await client.send_sms_verify_code_with_options_async(reks_req, runtime)
        print(sms_res)
        return True
    except Exception as e:
        print("验证码发送失败", e)
        return False


# Testing the function
asyncio.run(send_sms_code_async('13435176859'))
