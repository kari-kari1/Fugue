"""知识库 API 端点"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DatabaseSession
from app.models.memory import AgentKnowledgeMapping, Document, KnowledgeBase
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Pydantic Schemas ---


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str
    description: str | None = None
    embedding_model: str = "all-MiniLM-L6-v2"


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: str | None = None
    description: str | None = None


class AgentMappingOut(BaseModel):
    """Agent-知识库映射输出"""
    id: str
    agent_id: str
    knowledge_base_id: str

    model_config = {"from_attributes": True}


class KnowledgeBaseOut(BaseModel):
    """知识库输出"""
    id: str
    name: str
    description: str | None
    embedding_model: str | None = "all-MiniLM-L6-v2"
    document_count: int
    chunk_count: int
    agent_mappings: list[AgentMappingOut] | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentChunkIn(BaseModel):
    """手动添加文档块"""
    content: str
    metadata: dict | None = None


class ChunkBatchIn(BaseModel):
    """批量添加文档块请求"""
    chunks: list[DocumentChunkIn]


class AgentMappingIn(BaseModel):
    """Agent-知识库关联"""
    agent_id: str


# --- CRUD Endpoints ---


@router.get("/", response_model=list[KnowledgeBaseOut])
async def list_knowledge_bases(
    db: DatabaseSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取当前用户的知识库列表"""
    query = (
        select(KnowledgeBase)
        .where(KnowledgeBase.user_id == current_user.id)
        .options(selectinload(KnowledgeBase.agent_mappings))
        .order_by(KnowledgeBase.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.post("/", response_model=KnowledgeBaseOut)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """创建知识库"""
    knowledge_base = KnowledgeBase(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        embedding_model=data.embedding_model,
    )
    db.add(knowledge_base)
    await db.flush()

    # 创建 ChromaDB 向量集合（不可用时跳过）
    vector_store = get_vector_store()
    if vector_store:
        try:
            await vector_store.create_collection(str(knowledge_base.id))
        except Exception:
            logger.warning("Failed to create ChromaDB collection", exc_info=True)

    await db.commit()
    # 用 selectinload 重新加载，确保 agent_mappings 已加载
    result2 = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.id == knowledge_base.id)
        .options(selectinload(KnowledgeBase.agent_mappings))
    )
    return result2.scalar_one()


@router.get("/vector-store/status")
async def vector_store_status(current_user: CurrentUser):
    """检查向量存储可用状态"""
    vs = get_vector_store()
    available = vs is not None and vs.is_available()
    return {
        "available": available,
        "engine": "chromadb" if available else "sqlite-fallback",
        "message": (
            "向量存储正常运行"
            if available
            else "ChromaDB 未安装，知识库搜索使用 SQLite 全文查询（功能可用，精度较低）"
        ),
    }


@router.get("/{kb_id}", response_model=KnowledgeBaseOut)
async def get_knowledge_base(
    kb_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取知识库详情"""
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.id == kb_id, KnowledgeBase.user_id == current_user.id)
        .options(selectinload(KnowledgeBase.agent_mappings))
    )
    knowledge_base = result.scalar_one_or_none()
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return knowledge_base


@router.put("/{kb_id}", response_model=KnowledgeBaseOut)
async def update_knowledge_base(
    kb_id: str,
    data: KnowledgeBaseUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新知识库"""
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.id == kb_id, KnowledgeBase.user_id == current_user.id)
        .options(selectinload(KnowledgeBase.agent_mappings))
    )
    knowledge_base = result.scalar_one_or_none()
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    if data.name is not None:
        knowledge_base.name = data.name
    if data.description is not None:
        knowledge_base.description = data.description

    await db.commit()
    await db.refresh(knowledge_base)
    return knowledge_base


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除知识库（同时删除向量集合和所有文档）"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    knowledge_base = result.scalar_one_or_none()
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 删除 ChromaDB 向量集合（不可用时跳过）
    vector_store = get_vector_store()
    if vector_store:
        try:
            await vector_store.delete_collection(str(knowledge_base.id))
        except Exception:
            logger.warning("Failed to delete ChromaDB collection for kb %s", kb_id, exc_info=True)

    await db.delete(knowledge_base)
    await db.commit()
    return {"message": "知识库已删除"}


# --- 文档管理 ---


@router.get("/{kb_id}/documents")
async def list_documents(
    kb_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取知识库下的文档列表"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    doc_result = await db.execute(
        select(Document)
        .where(Document.knowledge_base_id == kb_id)
        .order_by(Document.created_at.desc())
    )
    docs = doc_result.scalars().all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type or "txt",
            "chunk_count": d.chunk_count or 0,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.post("/{kb_id}/chunks")
async def add_chunks(
    kb_id: str,
    body: ChunkBatchIn,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """向知识库添加文本块（同时创建文档记录）"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    knowledge_base = result.scalar_one_or_none()
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    chunks = body.chunks
    if not chunks:
        return {"added": 0}

    # 从 metadata 提取文件名，用于创建 Document 记录
    source_name = None
    if chunks[0].metadata:
        source_name = chunks[0].metadata.get("source")

    filename = source_name or f"manual_{uuid.uuid4().hex[:8]}.txt"
    file_ext = filename.rsplit(".", 1)[-1] if "." in filename else "txt"

    # 创建 Document 记录
    doc = Document(
        knowledge_base_id=kb_id,
        filename=filename,
        file_type=file_ext,
        file_size=sum(len(c.content) for c in chunks),
        chunk_count=len(chunks),
        metadata_={"source": source_name} if source_name else {},
    )
    db.add(doc)

    # 准备向量数据
    vector_docs = [
        {
            "id": f"chunk_{knowledge_base.id}_{uuid.uuid4().hex[:8]}_{i}",
            "content": chunk.content,
            "metadata": chunk.metadata or {},
        }
        for i, chunk in enumerate(chunks)
    ]

    # 写入向量存储（不可用时跳过）
    vector_store = get_vector_store()
    if vector_store:
        try:
            await vector_store.add_documents(str(knowledge_base.id), vector_docs)
        except Exception as e:
            logger.warning("Vector store add failed (non-fatal): %s", e)

    # 更新知识库统计
    knowledge_base.chunk_count = (knowledge_base.chunk_count or 0) + len(chunks)
    knowledge_base.document_count = (knowledge_base.document_count or 0) + 1

    await db.commit()
    await db.refresh(knowledge_base)

    return {"added": len(chunks), "document_id": doc.id, "filename": filename}


@router.get("/{kb_id}/search")
async def search_knowledge_base(
    kb_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
    query: str = Query(..., min_length=1, description="搜索文本"),
    top_k: int = Query(5, ge=1, le=50),
):
    """在知识库中搜索相似内容"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    vector_store = get_vector_store()
    if not vector_store:
        return {"results": [], "message": "向量存储不可用，语义搜索功能暂不可用"}

    try:
        results = await vector_store.search(
            knowledge_base_id=str(kb_id),
            query=query,
            top_k=top_k,
        )
    except Exception as e:
        logger.error("Search failed for kb %s: %s", kb_id, e)
        return {"results": [], "message": f"搜索失败: {str(e)}"}

    return {"results": results}


# --- Agent-知识库关联 ---


@router.get("/agent/{agent_id}/knowledge-bases", response_model=list[KnowledgeBaseOut])
async def list_agent_knowledge_bases(
    agent_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取指定 Agent 关联的所有知识库"""
    mappings_result = await db.execute(
        select(AgentKnowledgeMapping).where(
            AgentKnowledgeMapping.agent_id == agent_id,
        )
    )
    mappings = mappings_result.scalars().all()
    if not mappings:
        return []

    kb_ids = [m.knowledge_base_id for m in mappings]
    kbs_result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.id.in_(kb_ids), KnowledgeBase.user_id == current_user.id)
        .options(selectinload(KnowledgeBase.agent_mappings))
    )
    return kbs_result.scalars().all()


@router.post("/{kb_id}/agent-mappings")
async def create_agent_mapping(
    kb_id: str,
    data: AgentMappingIn,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """将知识库关联到 Agent"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    knowledge_base = result.scalar_one_or_none()
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 检查是否已存在
    existing = await db.execute(
        select(AgentKnowledgeMapping).where(
            AgentKnowledgeMapping.agent_id == data.agent_id,
            AgentKnowledgeMapping.knowledge_base_id == kb_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="该关联已存在")

    mapping = AgentKnowledgeMapping(
        agent_id=data.agent_id,
        knowledge_base_id=kb_id,
    )
    db.add(mapping)
    await db.flush()

    return {"id": mapping.id, "agent_id": data.agent_id, "knowledge_base_id": kb_id}


@router.get("/{kb_id}/agent-mappings")
async def list_agent_mappings(
    kb_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取知识库关联的 Agent 列表"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    mappings_result = await db.execute(
        select(AgentKnowledgeMapping).where(
            AgentKnowledgeMapping.knowledge_base_id == kb_id,
        )
    )
    return mappings_result.scalars().all()


@router.delete("/{kb_id}/agent-mappings/{mapping_id}")
async def delete_agent_mapping(
    kb_id: str,
    mapping_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除 Agent-知识库关联"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    mapping_result = await db.execute(
        select(AgentKnowledgeMapping).where(
            AgentKnowledgeMapping.id == mapping_id,
            AgentKnowledgeMapping.knowledge_base_id == kb_id,
        )
    )
    mapping = mapping_result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail="关联不存在")

    await db.delete(mapping)
    await db.commit()
    return {"message": "关联已删除"}


# ── Scope-based 记忆管理 API ──────────────────────────────


class ScopedMemorySave(BaseModel):
    """带scope的记忆保存请求"""
    crew_id: str
    agent_id: str
    content: str
    memory_type: str = "conclusion"
    importance: float = 1.0
    level: str = "agent"  # agent, task, shared


class MemoryTreeResponse(BaseModel):
    """记忆树响应"""
    project_id: str
    scopes: dict = {}
    total_memories: int = 0


@router.get("/memories/scope/{crew_id}")
async def get_memory_tree(
    crew_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取项目记忆scope树结构"""
    from app.services.memory_service import MemoryService
    service = MemoryService(db)
    tree = await service.memory_tree(crew_id)
    return tree


@router.get("/memories/scope/{crew_id}/{level}")
async def get_scoped_memories(
    crew_id: str,
    level: str,
    db: DatabaseSession,
    current_user: CurrentUser,
    agent_id: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """按scope检索记忆

    level: agent, task, shared
    可选 agent_id 参数用于精确到特定Agent
    """
    from app.services.memory_service import MemoryService
    service = MemoryService(db)

    if level == "shared":
        scope = MemoryService.build_scope(crew_id, "shared")
    else:
        scope = MemoryService.build_scope(crew_id, level, agent_id)

    memories = await service.recall_by_scope(scope, top_k=limit)
    return {
        "scope": scope,
        "memories": memories,
        "count": len(memories),
    }


@router.post("/memories/scoped")
async def save_scoped_memory(
    data: ScopedMemorySave,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """保存带scope的Agent记忆"""
    from app.services.memory_service import MemoryService
    service = MemoryService(db)

    scope = MemoryService.build_scope(data.crew_id, data.level, data.agent_id if data.level != "shared" else None)
    memory = await service.save_memory_scoped(
        agent_id=data.agent_id,
        content=data.content,
        scope=scope,
        memory_type=data.memory_type,
        importance=data.importance,
    )

    return {
        "id": str(memory.id),
        "agent_id": data.agent_id,
        "scope": scope,
        "content": data.content[:200],
        "memory_type": data.memory_type,
    }


@router.delete("/memories/scoped/{crew_id}/{level}")
async def forget_scoped_memories(
    crew_id: str,
    level: str,
    db: DatabaseSession,
    current_user: CurrentUser,
    agent_id: str = Query(None),
):
    """删除指定scope下的所有记忆"""
    from app.services.memory_service import MemoryService
    service = MemoryService(db)

    scope = MemoryService.build_scope(crew_id, level, agent_id if level != "shared" else None)
    count = await service.forget_by_scope(scope)

    return {
        "scope": scope,
        "deleted_count": count,
        "message": f"已删除 {count} 条记忆",
    }
