"""数据库连接和会话管理 — 支持 SQLite（桌面）和 PostgreSQL（服务器）"""

import asyncio
import logging
from typing import AsyncGenerator, Optional
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)

# A7: SQLite 写入锁 — 确保同一时刻只有一个写操作
_write_lock = asyncio.Lock()


def _is_sqlite(url: str) -> bool:
    """检测是否使用 SQLite"""
    return url.startswith("sqlite")


# 基础模型类
class Base(DeclarativeBase):
    pass


# 全局变量存储引擎和会话工厂
_engine = None
_async_session_factory = None


def get_engine():
    """获取数据库引擎（延迟初始化，自动适配 SQLite/PostgreSQL）"""
    global _engine
    if _engine is None:
        url = settings.DATABASE_URL
        if _is_sqlite(url):
            # A1+A6: SQLite — StaticPool + check_same_thread
            from sqlalchemy.pool import StaticPool
            _engine = create_async_engine(
                url,
                echo=settings.DEBUG,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
            # A7+A8: 注册 PRAGMA — WAL 模式 + 外键约束
            @event.listens_for(_engine.sync_engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.close()
            logger.info(f"SQLite engine initialized: {url}")
        else:
            # PostgreSQL — 连接池
            _engine = create_async_engine(
                url,
                echo=settings.DEBUG,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
            )
            logger.info(f"PostgreSQL engine initialized")
    return _engine


def get_session_factory():
    """获取异步会话工厂（延迟初始化）"""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


# 向后兼容
def get_engine_compat():
    return get_engine()


class DatabaseSessionManager:
    """数据库会话管理器，支持不同的事件循环"""

    def __init__(self):
        self._engines = {}
        self._session_factories = {}

    def _create_engine_for_url(self, url: str):
        """创建引擎（自动适配 SQLite/PostgreSQL）"""
        if _is_sqlite(url):
            from sqlalchemy.pool import StaticPool
            engine = create_async_engine(
                url,
                echo=settings.DEBUG,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            engine = create_async_engine(
                url,
                echo=settings.DEBUG,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
            )
        return engine

    def get_engine_for_loop(self, loop: asyncio.AbstractEventLoop = None):
        """获取适用于当前事件循环的引擎

        E10 注意: 使用 id(loop) 作为缓存键，在 loop 被 GC 后 id 可能被复用。
        桌面模式下仅使用单个事件循环，此限制可接受。
        """
        if loop is None:
            loop = asyncio.get_event_loop()

        loop_id = id(loop)
        if loop_id not in self._engines:
            self._engines[loop_id] = self._create_engine_for_url(settings.DATABASE_URL)
        return self._engines[loop_id]

    def get_session_factory_for_loop(self, loop: asyncio.AbstractEventLoop = None):
        """获取适用于当前事件循环的会话工厂

        E10 注意: 与 get_engine_for_loop 相同的 id(loop) 限制。
        """
        if loop is None:
            loop = asyncio.get_event_loop()

        loop_id = id(loop)
        if loop_id not in self._session_factories:
            engine = self.get_engine_for_loop(loop)
            self._session_factories[loop_id] = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_factories[loop_id]

    @asynccontextmanager
    async def get_session(self, loop: asyncio.AbstractEventLoop = None):
        """获取数据库会话（上下文管理器）"""
        session_factory = self.get_session_factory_for_loop(loop)
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def reset_for_testing(self, database_url: str = None):
        """测试专用：重置会话管理器以使用指定的数据库URL

        Args:
            database_url: 新的数据库URL，None时使用settings.DATABASE_URL
        """
        if database_url:
            # 更新settings以便新创建的引擎使用
            import app.core.config
            app.core.config.settings.DATABASE_URL = database_url
        self._engines.clear()
        self._session_factories.clear()

    async def close_all(self):
        """关闭所有引擎"""
        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()
        self._session_factories.clear()


# 全局会话管理器
db_session_manager = DatabaseSessionManager()


# 向后兼容的 AsyncSessionLocal
class AsyncSessionLocalProxy:
    """AsyncSessionLocal 的代理，支持上下文管理器"""

    def __call__(self):
        return db_session_manager.get_session()

    def __getattr__(self, name):
        factory = get_session_factory()
        return getattr(factory, name)


AsyncSessionLocal = AsyncSessionLocalProxy()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入"""
    async with db_session_manager.get_session() as session:
        yield session


async def get_db_with_write_lock() -> AsyncGenerator[AsyncSession, None]:
    """获取带写入锁的数据库会话（SQLite 并发安全）"""
    async with _write_lock:
        async with db_session_manager.get_session() as session:
            yield session


async def _migrate_sqlite_columns(engine):
    """SQLite 不支持 IF NOT EXISTS ADD COLUMN，用 PRAGMA 检查后添加"""
    import sqlalchemy as sa
    try:
        async with engine.begin() as conn:
            # tasks.config
            result = await conn.execute(sa.text("PRAGMA table_info(tasks)"))
            columns = [row[1] for row in result.fetchall()]
            if 'config' not in columns:
                await conn.execute(sa.text("ALTER TABLE tasks ADD COLUMN config JSON"))
                logger.info("Migration: added 'config' column to tasks table")

            # crews.workspace_dir（工作空间功能）
            result_crew = await conn.execute(sa.text("PRAGMA table_info(crews)"))
            crew_cols = [row[1] for row in result_crew.fetchall()]
            if 'workspace_dir' not in crew_cols:
                await conn.execute(sa.text("ALTER TABLE crews ADD COLUMN workspace_dir VARCHAR(500)"))
                logger.info("Migration: added 'workspace_dir' column to crews table")

            # executions.llm_api_keys / llm_base_urls（迭代优化需要）
            result2 = await conn.execute(sa.text("PRAGMA table_info(executions)"))
            exec_cols = [row[1] for row in result2.fetchall()]
            if 'llm_api_keys' not in exec_cols:
                await conn.execute(sa.text("ALTER TABLE executions ADD COLUMN llm_api_keys JSON"))
                logger.info("Migration: added 'llm_api_keys' column to executions table")
            if 'llm_base_urls' not in exec_cols:
                await conn.execute(sa.text("ALTER TABLE executions ADD COLUMN llm_base_urls JSON"))
                logger.info("Migration: added 'llm_base_urls' column to executions table")
            if 'worktree_path' not in exec_cols:
                await conn.execute(sa.text("ALTER TABLE executions ADD COLUMN worktree_path VARCHAR(500)"))
                logger.info("Migration: added 'worktree_path' column to executions table")
            if 'sandbox_type' not in exec_cols:
                await conn.execute(sa.text("ALTER TABLE executions ADD COLUMN sandbox_type VARCHAR(20)"))
                logger.info("Migration: added 'sandbox_type' column to executions table")

            # crews.project_memory（分层项目记忆）
            if 'project_memory' not in crew_cols:
                await conn.execute(sa.text("ALTER TABLE crews ADD COLUMN project_memory TEXT"))
                logger.info("Migration: added 'project_memory' column to crews table")

            # agents.agent_experience（Agent经验）
            result_agent = await conn.execute(sa.text("PRAGMA table_info(agents)"))
            agent_cols = [row[1] for row in result_agent.fetchall()]
            if 'agent_experience' not in agent_cols:
                await conn.execute(sa.text("ALTER TABLE agents ADD COLUMN agent_experience TEXT"))
                logger.info("Migration: added 'agent_experience' column to agents table")

            # memory_configs.chunk_size / chunk_overlap（RAG分块配置）
            try:
                result_mc = await conn.execute(sa.text("PRAGMA table_info(memory_configs)"))
                mc_cols = [row[1] for row in result_mc.fetchall()]
                if 'chunk_size' not in mc_cols:
                    await conn.execute(sa.text("ALTER TABLE memory_configs ADD COLUMN chunk_size INTEGER DEFAULT 500"))
                    logger.info("Migration: added 'chunk_size' column to memory_configs table")
                if 'chunk_overlap' not in mc_cols:
                    await conn.execute(sa.text("ALTER TABLE memory_configs ADD COLUMN chunk_overlap INTEGER DEFAULT 50"))
                    logger.info("Migration: added 'chunk_overlap' column to memory_configs table")
            except Exception:
                pass

            # agent_memories.scope（scope路径式记忆）
            try:
                result_mem = await conn.execute(sa.text("PRAGMA table_info(agent_memories)"))
                mem_cols = [row[1] for row in result_mem.fetchall()]
                if 'scope' not in mem_cols:
                    await conn.execute(sa.text("ALTER TABLE agent_memories ADD COLUMN scope VARCHAR(500)"))
                    logger.info("Migration: added 'scope' column to agent_memories table")
                if 'recency_weight' not in mem_cols:
                    await conn.execute(sa.text("ALTER TABLE agent_memories ADD COLUMN recency_weight FLOAT DEFAULT 1.0"))
                    logger.info("Migration: added 'recency_weight' column to agent_memories table")
            except Exception:
                # agent_memories 表可能尚不存在（首次运行）
                pass

    except Exception as e:
        logger.warning(f"Migration check failed (may be first run): {e}")


async def init_db():
    """初始化数据库（创建所有表）"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if _is_sqlite(settings.DATABASE_URL):
        logger.info("SQLite tables created via create_all")
        await _migrate_sqlite_columns(engine)


def get_engine_for_celery():
    """专门为 Celery worker 获取引擎"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return db_session_manager.get_engine_for_loop(loop)


def get_session_factory_for_celery():
    """专门为 Celery worker 获取会话工厂"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return db_session_manager.get_session_factory_for_loop(loop)


async def close_db():
    """关闭数据库连接"""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    _async_session_factory = None
    await db_session_manager.close_all()
