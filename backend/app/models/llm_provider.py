"""LLM提供商配置模型"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from app.models.base import BaseModel


class LLMProvider(BaseModel):
    """LLM提供商配置"""

    __tablename__ = "llm_providers"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # NULL=平台默认
    provider = Column(String(50), nullable=False)  # openai, anthropic, google, ollama, custom
    display_name = Column(String(255), nullable=True)
    api_key_encrypted = Column(String(500), nullable=True)  # 加密存储
    api_key_hash = Column(String(100), nullable=True)  # 哈希用于去重
    base_url = Column(String(500), nullable=True)  # 自定义API地址
    default_model = Column(String(100), nullable=True)
    is_platform_default = Column(Boolean, default=False)

    # 限流配置
    rate_limit_rpm = Column(Integer, default=60)  # 每分钟请求数
    rate_limit_tpm = Column(Integer, default=60000)  # 每分钟Token数

    # 预算控制
    monthly_budget_usd = Column(Float, nullable=True)
    current_month_usage_usd = Column(Float, default=0.0)
    usage_alert_threshold = Column(Float, default=0.8)  # 80%时告警

    # 健康检查
    last_health_check = Column(String(50), nullable=True)
    is_healthy = Column(Boolean, default=True)
    consecutive_failures = Column(Integer, default=0)

    def __repr__(self):
        return f"<LLMProvider {self.provider} ({self.display_name})>"
