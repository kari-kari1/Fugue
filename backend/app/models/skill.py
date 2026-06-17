"""Skills 数据库模型 — 报告第6章：技能功能扩展"""

from sqlalchemy import JSON, Boolean, Column, String, Text

from app.models.base import BaseModel


class Skill(BaseModel):
    """技能模型 — 可重用的任务模板，支持导入/导出/沙箱执行"""

    __tablename__ = "skills"

    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), default="1.0.0")
    author = Column(String(255), nullable=True)
    author_url = Column(String(500), nullable=True)
    license = Column(String(50), default="MIT")
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    config = Column(JSON, default=dict)  # 技能元数据（参数定义、入口点等）
    code_path = Column(String(500), nullable=True)  # 技能代码存储路径
    entrypoint = Column(JSON, default=dict)  # {"file": "handler.py", "params": {...}}
    required_tools = Column(JSON, default=list)  # 依赖的工具列表
    prompt_template = Column(Text, nullable=True)  # Jinja-style 提示模板
    task_template = Column(JSON, default=dict)  # 预配置的任务定义
    active = Column(Boolean, default=True)
    is_builtin = Column(Boolean, default=False)
    install_count = Column(String, default="0")  # 使用 Text 避免 SQLite JSON 问题
    star_count = Column(String, default="0")
    verified = Column(Boolean, default=False)
    metadata_ = Column("metadata", JSON, default=dict)

    def __repr__(self):
        return f"<Skill {self.name} v{self.version}>"
