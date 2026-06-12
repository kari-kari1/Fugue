"""插件配置模型"""

from sqlalchemy import Column, String, JSON, Boolean, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PluginConfig(BaseModel):
    """插件配置（用户安装的插件）"""

    __tablename__ = "plugin_configs"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    crew_id = Column(String(36), ForeignKey("crews.id", ondelete="CASCADE"), nullable=True, index=True)

    # 插件标识
    plugin_name = Column(String(100), nullable=False, index=True, comment="插件名称")
    plugin_version = Column(String(20), nullable=False, comment="插件版本")

    # 配置
    enabled = Column(Boolean, default=True, comment="是否启用")
    config = Column(JSON, default=dict, comment="插件配置")
    permissions_approved = Column(JSON, default=list, comment="已批准的权限列表")

    # 来源
    source = Column(String(50), default="local", comment="来源：local/marketplace/github")
    source_url = Column(String(500), nullable=True, comment="来源URL")

    # 关系
    user = relationship("User", back_populates="plugins")
    crew = relationship("Crew", back_populates="plugins")

    def __repr__(self):
        return f"<PluginConfig {self.plugin_name} v{self.plugin_version}>"


class PluginMarketplace(BaseModel):
    """插件市场（插件发布信息）"""

    __tablename__ = "plugin_marketplace"

    # 插件信息
    plugin_name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(200), nullable=False, comment="显示名称")
    description = Column(Text, nullable=False, comment="插件描述")
    long_description = Column(Text, nullable=True, comment="详细描述（Markdown）")

    # 版本信息
    current_version = Column(String(20), nullable=False)
    min_fugue_version = Column(String(20), nullable=True, comment="最低Fugue版本")

    # 作者信息
    author = Column(String(100), nullable=False)
    author_email = Column(String(200), nullable=True)
    homepage = Column(String(500), nullable=True)
    repository = Column(String(500), nullable=True, comment="GitHub仓库")

    # 分类和标签
    category = Column(String(50), default="general", comment="分类：search/file/data/code/ai/general")
    tags = Column(JSON, default=list, comment="标签列表")

    # 安装信息
    install_command = Column(String(500), nullable=True, comment="安装命令")
    dependencies = Column(JSON, default=list, comment="依赖列表")
    python_requires = Column(String(50), default=">=3.10")

    # 工具信息
    tools_list = Column(JSON, default=list, comment="提供的工具列表")
    permissions_required = Column(JSON, default=list, comment="所需权限")

    # 统计
    download_count = Column(Integer, default=0, comment="下载次数")
    star_count = Column(Integer, default=0, comment="Star数量")
    rating = Column(Integer, default=0, comment="评分（0-500，代表0.00-5.00）")

    # 状态
    status = Column(String(20), default="active", comment="状态：active/deprecated/banned")
    verified = Column(Boolean, default=False, comment="官方认证")

    # 发布者
    publisher_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    publisher = relationship("User", back_populates="published_plugins")

    def __repr__(self):
        return f"<PluginMarketplace {self.plugin_name} v{self.current_version}>"

    def to_dict(self):
        return {
            "plugin_name": self.plugin_name,
            "display_name": self.display_name,
            "description": self.description,
            "current_version": self.current_version,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "download_count": self.download_count,
            "star_count": self.star_count,
            "rating": self.rating / 100,
            "verified": self.verified,
            "tools_count": len(self.tools_list) if self.tools_list else 0,
        }


class PluginVersion(BaseModel):
    """插件版本历史"""

    __tablename__ = "plugin_versions"

    plugin_name = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False)

    # 版本信息
    changelog = Column(Text, nullable=True, comment="更新日志")
    release_notes = Column(Text, nullable=True, comment="发布说明")

    # 下载信息
    download_url = Column(String(500), nullable=True)
    file_hash = Column(String(64), nullable=True, comment="文件SHA256哈希")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")

    # 状态
    is_prerelease = Column(Boolean, default=False)
    is_deprecated = Column(Boolean, default=False)

    # 发布时间
    published_at = Column(String(30), nullable=True)  # ISO格式时间

    def __repr__(self):
        return f"<PluginVersion {self.plugin_name} v{self.version}>"
