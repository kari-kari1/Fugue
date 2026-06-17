"""用户相关Schema — 报告 P0-1: 添加密码强度校验"""

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """用户基础Schema"""
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=50)
    full_name: str | None = None

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_一-鿿]+$', v):
            raise ValueError("用户名只能包含字母、数字、下划线和中文")
        return v


class UserCreate(UserBase):
    """创建用户 — 报告要求: 8位以上含大小写数字特殊字符"""
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r'[a-z]', v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not re.search(r'\d', v):
            raise ValueError("密码必须包含至少一个数字")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', v):
            raise ValueError("密码必须包含至少一个特殊字符")
        return v


class UserLogin(BaseModel):
    """用户登录"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """更新用户"""
    full_name: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    """用户响应"""
    id: str
    is_active: bool
    is_superuser: bool
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token载荷"""
    sub: str
    exp: datetime


class TokenInfo(BaseModel):
    """Token信息"""
    remaining_seconds: int
    is_expiring_soon: bool


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    reset_token: str
    new_password: str = Field(..., min_length=8)
