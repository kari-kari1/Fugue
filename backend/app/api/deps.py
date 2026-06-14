"""API依赖注入"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_superuser, get_current_user
from app.models.user import User

# 数据库会话依赖
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]

# 当前用户依赖
CurrentUser = Annotated[User, Depends(get_current_user)]

# 当前超级管理员依赖
CurrentSuperUser = Annotated[User, Depends(get_current_superuser)]
