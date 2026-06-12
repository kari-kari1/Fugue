"""用户相关Schema"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """用户基础Schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """用户登录"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """更新用户"""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """用户响应"""
    id: str
    is_active: bool
    is_superuser: bool
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
