"""记忆与知识库模型"""

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class MemoryConfig(BaseModel):
    """记忆配置"""

    __tablename__ = "memory_configs"

    crew_id = Column(String(36), ForeignKey("crews.id", ondelete="CASCADE"), nullable=False, index=True)

    # 短期记忆配置
    short_term_enabled = Column(Boolean, default=True)
    short_term_window = Column(Integer, default=10, comment="短期记忆窗口大小")

    # 长期记忆配置
    long_term_enabled = Column(Boolean, default=True)
    vector_store_type = Column(String(20), default="chromadb", comment="向量存储类型")
    retrieval_strategy = Column(String(20), default="hybrid", comment="检索策略: semantic/hybrid")
    top_k = Column(Integer, default=5, comment="检索结果数量")
    chunk_size = Column(Integer, default=500, comment="文档分块大小(字符)")
    chunk_overlap = Column(Integer, default=50, comment="分块重叠大小(字符)")

    # P1: 自动索引配置
    auto_index_on_complete = Column(Boolean, default=True, comment="任务完成后自动索引输出到知识库")

    # 关联
    crew = relationship("Crew", back_populates="memory_configs")

    def __repr__(self):
        return f"<MemoryConfig crew_id={self.crew_id}>"


class KnowledgeBase(BaseModel):
    """知识库"""

    __tablename__ = "knowledge_bases"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    embedding_model = Column(String(50), default="all-MiniLM-L6-v2")

    # 统计
    document_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)

    # 关联
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    agent_mappings = relationship("AgentKnowledgeMapping", back_populates="knowledge_base", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KnowledgeBase {self.name}>"


class Document(BaseModel):
    """文档"""

    __tablename__ = "documents"

    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)

    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)

    # 元数据
    metadata_ = Column("metadata", JSON, default=dict)

    # 关联
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.filename}>"


class AgentKnowledgeMapping(BaseModel):
    """Agent-知识库映射"""

    __tablename__ = "agent_knowledge_mappings"

    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)

    # 关联
    knowledge_base = relationship("KnowledgeBase", back_populates="agent_mappings")

    def __repr__(self):
        return f"<AgentKnowledgeMapping agent={self.agent_id} kb={self.knowledge_base_id}>"


class AgentMemory(BaseModel):
    """Agent 长期记忆 — 跨执行持久化记忆"""

    __tablename__ = "agent_memories"

    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_id = Column(String(36), ForeignKey("executions.id", ondelete="SET NULL"), nullable=True)

    content = Column(Text, nullable=False, comment="记忆内容")
    memory_type = Column(String(20), default="conclusion", comment="记忆类型: conclusion/feedback/pattern")
    importance = Column(Float, default=1.0, comment="重要性权重 0-5")
    recency_weight = Column(Float, default=1.0, comment="时效性衰减权重，初始1.0，随时间递减")
    scope = Column(String(500), nullable=True, index=True, comment="路径式scope: /project/{crew_id}/agent/{agent_id} 或 /project/{crew_id}/shared")
    metadata_ = Column("metadata", JSON, default=dict, comment="额外元数据")

    def __repr__(self):
        return f"<AgentMemory agent={self.agent_id} type={self.memory_type}>"
