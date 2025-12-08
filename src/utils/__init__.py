import re


@staticmethod
def phoneRegex(phone:str):
    pattern = r'^(13[0-9]|14[5-9]|15[0-3,5-9]|16[6]|17[0-8]|18[0-9]|19[8,9])\d{8}$'
    if re.match(pattern, phone):
        return {'result': True, 'msg': "手机号格式正确"}
    else:
        return {'result': False, 'msg': "手机号格式不正确"}
