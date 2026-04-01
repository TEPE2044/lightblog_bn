from typing import Optional


def rback(status: int, msg: str, data: Optional[any] = None):
    return {
        "status": status,
        "msg": msg,
        "data": data
    }


