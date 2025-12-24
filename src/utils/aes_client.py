import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from src.config import settings


# 手机加密，使用AES-GCM
# 96 bit nonce
async def encrypt_phone(phone: str) -> str:
    iv = get_random_bytes(12)
    cipher = AES.new(bytes.fromhex(settings.aes_secret), AES.MODE_GCM, nonce=iv)
    cipher.update(b"")  # 附加数据（留空）
    ciphertext, tag = cipher.encrypt_and_digest(phone.encode())
    return base64.urlsafe_b64encode(iv + ciphertext + tag).decode().rstrip("=")


# 手机解密
async def decrypt_phone(b64: str) -> str:
    data = base64.urlsafe_b64decode(b64 + "==")
    iv, ciphertext, tag = data[:12], data[12:-16], data[-16:]
    cipher = AES.new(bytes.fromhex(settings.aes_secret), AES.MODE_GCM, nonce=iv)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()
