# 半年执行一次
# 已执行的用户，token自然死亡即可
from Crypto.Random import get_random_bytes

KEY = get_random_bytes(32)
print(KEY.hex())

