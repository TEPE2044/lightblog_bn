from typing import Optional


class Rback:
    def __init__(self):
        self.status = 0
        self.msg = None
        self.data = None

    def back_msg(self, status: int, msg: str, data: Optional[any] = None):
        return {
            status: status,
            msg: msg,
            data: data
        }
