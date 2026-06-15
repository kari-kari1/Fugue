"""认证相关API"""

from datetime import timedelta, datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select

from app.api.deps import DatabaseSession, CurrentUser, CurrentSuperUser
from fastapi.security import HTTPBearer
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_token_remaining_seconds,
)
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token, TokenInfo,
    ForgotPasswordRequest, ResetPasswordRequest,
)

router = APIRouter()
security = HTTPBearer()

# 内存中的密码重置Token存储: {token: {"user_id": str, "expires_at": datetime}}
reset_tokens: dict[str, dict] = {}

# B15: 登录失败尝试追踪: {email: {"count": int, "first_attempt": datetime}}
_failed_login_attempts: dict[str, dict] = {}
_MAX_FAILED_ATTEMPTS = 5
_FAILED_ATTEMPTS_WINDOW = timedelta(minutes=15)

# B13: 密码重置请求追踪: {email: {"count": int, "window_start": datetime}}
_reset_request_counts: dict[str, dict] = {}
_MAX_RESET_REQUESTS = 3
_RESET_REQUEST_WINDOW = timedelta(minutes=15)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """获取当前登录用户信息"""
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: DatabaseSession):
    """用户注册"""
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )

    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已被使用",
        )

    # 创建用户（IntegrityError由全局异常处理器捕获，返回400）
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: DatabaseSession):
    """用户登录"""
    # B15: 登录失败次数限制
    email_key = login_data.email.lower()
    now = datetime.now(timezone.utc)
    attempt = _failed_login_attempts.get(email_key)
    if attempt and (now - attempt["first_attempt"]) < _FAILED_ATTEMPTS_WINDOW:
        if attempt["count"] >= _MAX_FAILED_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="登录失败次数过多，请15分钟后再试",
            )
    elif attempt and (now - attempt["first_attempt"]) >= _FAILED_ATTEMPTS_WINDOW:
        # 窗口已过期，重置
        del _failed_login_attempts[email_key]

    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        # B15: 记录失败尝试
        attempt = _failed_login_attempts.get(email_key)
        if attempt and (now - attempt["first_attempt"]) < _FAILED_ATTEMPTS_WINDOW:
            attempt["count"] += 1
        else:
            _failed_login_attempts[email_key] = {"count": 1, "first_attempt": now}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # B15: 登录成功，清除失败记录
    _failed_login_attempts.pop(email_key, None)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": access_token, "token_type": "bearer", "expires_in": expires_seconds}


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: CurrentUser):
    """刷新当前用户的访问令牌"""
    expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": access_token, "token_type": "bearer", "expires_in": expires_seconds}


@router.get("/token-info", response_model=TokenInfo)
async def token_info(current_user: CurrentUser, credentials=Depends(security)):
    """获取当前Token的过期信息"""
    token = credentials.credentials
    remaining = get_token_remaining_seconds(token)

    return {
        "remaining_seconds": remaining,
        "is_expiring_soon": remaining < 300,
    }


# ──────────────────────────────────────────────
# 密码重置
# ──────────────────────────────────────────────

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: DatabaseSession):
    """发起密码重置（生成token，15分钟有效；暂不发邮件）"""
    # B13: 密码重置频率限制 — 每个邮箱15分钟内最多3次
    email_key = req.email.lower()
    now = datetime.now(timezone.utc)
    rc = _reset_request_counts.get(email_key)
    if rc and (now - rc["window_start"]) < _RESET_REQUEST_WINDOW:
        if rc["count"] >= _MAX_RESET_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="重置请求过于频繁，请15分钟后再试",
            )
        rc["count"] += 1
    elif rc and (now - rc["window_start"]) >= _RESET_REQUEST_WINDOW:
        _reset_request_counts[email_key] = {"count": 1, "window_start": now}
    else:
        _reset_request_counts[email_key] = {"count": 1, "window_start": now}

    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    # 不泄露用户是否存在，总是返回成功
    if not user:
        return {"message": "如果该邮箱已注册，重置链接将在15分钟内发送至邮箱"}

    token = uuid4().hex
    reset_tokens[token] = {
        "user_id": user.id,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
    }

    # 安全：不返回 reset_token，仅提示邮件已发送
    return {"message": "如果该邮箱已注册，重置链接将在15分钟内发送至邮箱"}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: DatabaseSession):
    """使用重置Token重置密码"""
    entry = reset_tokens.get(req.reset_token)
    if not entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效或已过期的重置Token")

    if datetime.now(timezone.utc) > entry["expires_at"]:
        del reset_tokens[req.reset_token]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效或已过期的重置Token")

    user_id = entry["user_id"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        del reset_tokens[req.reset_token]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在")

    user.hashed_password = get_password_hash(req.new_password)
    await db.flush()

    del reset_tokens[req.reset_token]

    return {"message": "密码重置成功"}


# ──────────────────────────────────────────────
# 管理员接口
# ──────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
async def list_users(db: DatabaseSession, admin: CurrentSuperUser):
    """列出所有用户（仅管理员）"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.patch("/users/{user_id}/toggle-superuser", response_model=UserResponse)
async def toggle_superuser(user_id: str, db: DatabaseSession, admin: CurrentSuperUser):
    """切换用户的超级管理员状态（仅管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user.is_superuser = not user.is_superuser
    await db.flush()
    await db.refresh(user)

    return user
