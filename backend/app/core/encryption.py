"""敏感数据加密存储

报告第一章 安全 (6/10) 建议:
- API Key 等敏感字段使用 Fernet 对称加密
- 加密密钥从环境变量或 SECRET_KEY 派生
"""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """从 SECRET_KEY 派生 Fernet 实例（懒加载）"""
    global _fernet
    if _fernet is None:
        # 用 SECRET_KEY 派生一个 32 字节的 Fernet 密钥
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        _fernet = Fernet(fernet_key)
    return _fernet


def encrypt(plaintext: str) -> str:
    """加密字符串 → base64 密文"""
    if not plaintext:
        return plaintext
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """解密 base64 密文 → 明文"""
    if not ciphertext:
        return ciphertext
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except Exception:
        logger.warning("Decrypt failed — data may be corrupted or tampered")
        raise ValueError("解密失败：数据损坏或密钥不匹配") from None


def is_encrypted(value: str) -> bool:
    """检查字符串是否是 Fernet 密文"""
    if not value:
        return False
    try:
        _get_fernet().decrypt(value.encode())
        return True
    except Exception:
        return False
