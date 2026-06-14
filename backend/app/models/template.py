from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String, Text

from app.models.base import BaseModel


class Template(BaseModel):
    """工作流模板模型"""
    __tablename__ = "templates"

    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    category = Column(String(50), index=True, comment="分类：research/code/analysis/document/literature")
    icon = Column(String(50), comment="图标标识（emoji）")
    difficulty = Column(String(20), comment="难度：beginner/intermediate/advanced")

    # 模板配置（JSON格式存储工作流结构）
    agents_config = Column(JSON, nullable=False, comment="Agent 配置列表")
    tasks_config = Column(JSON, nullable=False, comment="Task 配置列表")
    connections_config = Column(JSON, default=list, comment="连接关系")
    process_type = Column(String(20), default="sequential", comment="执行模式：sequential/parallel")

    # 元数据
    tags = Column(JSON, default=list, comment="标签列表")
    use_count = Column(Integer, default=0, comment="使用次数")
    rating = Column(Float, default=4.8, comment="评分（1-5）")
    rating_count = Column(Integer, default=0, comment="评分人数")
    is_builtin = Column(Boolean, default=True, comment="是否内置模板")
    is_public = Column(Boolean, default=False, comment="是否公开分享")
    user_id = Column(String(36), nullable=True, index=True, comment="创建者用户ID（用户自定义模板）")

    # 市场功能字段
    star_count = Column(Integer, default=0, comment="收藏次数")
    fork_count = Column(Integer, default=0, comment="Fork次数")
    forked_from_id = Column(String(36), ForeignKey("templates.id"), nullable=True, comment="Fork来源模板ID")

    def __repr__(self):
        return f"<Template {self.name}>"
