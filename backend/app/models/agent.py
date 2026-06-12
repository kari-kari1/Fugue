"""Agent（智能体）模型"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Agent(BaseModel):
    """智能体模型"""

    __tablename__ = "agents"

    crew_id = Column(String(36), ForeignKey("crews.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    goal = Column(Text, nullable=False)
    backstory = Column(Text, nullable=True)

    # LLM配置
    llm_provider = Column(String(50), default="openai")  # openai, anthropic, ollama, etc.
    llm_model = Column(String(100), default="gpt-4o")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)

    # Agent配置
    allow_delegation = Column(Boolean, default=False)
    max_iterations = Column(Integer, default=10)
    system_prompt_template = Column(Text, nullable=True)

    # Agent级经验记忆
    agent_experience = Column(Text, nullable=True, comment="Agent级经验文件，存储该Agent的最佳实践、已有知识等")

    # 工具配置
    tools_config = Column(JSON, default=list)  # 工具ID列表

    # 位置信息（用于画布渲染）
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)

    # 关系
    crew = relationship("Crew", back_populates="agents")
    tasks = relationship("Task", back_populates="agent")

    def __repr__(self):
        return f"<Agent {self.name} ({self.role})>"
