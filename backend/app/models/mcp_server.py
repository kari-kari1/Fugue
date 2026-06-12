"""MCP Server 配置模型"""

from sqlalchemy import Column, String, JSON, Boolean, ForeignKey

from app.models.base import BaseModel


class MCPServer(BaseModel):
    """MCP Server 配置"""

    __tablename__ = "mcp_servers"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    crew_id = Column(String(36), ForeignKey("crews.id", ondelete="CASCADE"), nullable=True, index=True)

    name = Column(String(100), nullable=False, comment="显示名称")
    command = Column(String(255), nullable=False, comment="启动命令（如 npx, python）")
    args = Column(JSON, default=list, comment="命令参数")
    env = Column(JSON, default=dict, comment="环境变量")
    enabled = Column(Boolean, default=True, comment="是否启用")

    # 缓存的工具列表（连接后更新）
    tools_cache = Column(JSON, default=list, comment="已发现的工具列表")

    def __repr__(self):
        return f"<MCPServer {self.name} ({self.command})>"
