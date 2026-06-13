"""记忆服务（短期记忆 + 长期记忆 RAG）"""

import logging
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import MemoryConfig, AgentKnowledgeMapping, AgentMemory
from app.models.execution import TaskExecution
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class MemoryService:
    """记忆服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_store = get_vector_store()

    async def get_context_window(
        self,
        execution_id: str,
        window_size: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取短期记忆（上下文窗口）

        从执行历史中获取最近完成的任务结果，作为短期记忆。

        Args:
            execution_id: 执行实例ID
            window_size: 窗口大小

        Returns:
            最近的任务执行结果列表（按时间正序）
        """
        result = await self.db.execute(
            select(TaskExecution)
            .where(
                TaskExecution.execution_id == execution_id,
                TaskExecution.output.isnot(None),
            )
            .order_by(TaskExecution.completed_at.desc())
            .limit(window_size)
        )
        recent_tasks = result.scalars().all()

        return [
            {
                "task_id": str(te.task_id),
                "agent_id": str(te.agent_id) if te.agent_id else None,
                "result": te.output,
                "timestamp": te.completed_at.isoformat() if te.completed_at else None,
            }
            for te in reversed(recent_tasks)
        ]

    async def retrieve_from_knowledge_base(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5,
        strategy: str = "hybrid",
    ) -> List[Dict[str, Any]]:
        """从知识库检索相关文档（RAG）— 支持语义/混合检索

        Args:
            agent_id: 智能体ID
            query: 查询文本
            top_k: 返回结果数量
            strategy: 检索策略 (semantic / hybrid), hybrid 合并向量+BM25

        Returns:
            相关文档列表
        """
        import asyncio as _aio

        result = await self.db.execute(
            select(AgentKnowledgeMapping)
            .where(AgentKnowledgeMapping.agent_id == agent_id)
        )
        mappings = result.scalars().all()

        if not mappings:
            return []

        # 并行搜索所有知识库（支持 hybrid 混合检索）
        async def _search_one(mapping):
            try:
                if strategy == "hybrid":
                    return await _aio.wait_for(
                        self.vector_store.hybrid_search(
                            knowledge_base_id=str(mapping.knowledge_base_id),
                            query=query,
                            top_k=top_k,
                            semantic_weight=0.7,
                        ),
                        timeout=5,
                    )
                else:
                    return await _aio.wait_for(
                        self.vector_store.search(
                            knowledge_base_id=str(mapping.knowledge_base_id),
                            query=query,
                            top_k=top_k,
                        ),
                        timeout=5,
                    )
            except _aio.TimeoutError:
                logger.warning("KB search timed out for %s", mapping.knowledge_base_id)
                return []
            except Exception:
                logger.warning("Failed to search KB %s for agent %s", mapping.knowledge_base_id, agent_id, exc_info=True)
                return []

        results_list = await _aio.gather(*[_search_one(m) for m in mappings])
        all_results = [r for sublist in results_list for r in sublist]

        # 按距离排序并返回 top_k
        all_results.sort(key=lambda x: x.get("distance", 0))
        return all_results[:top_k]

    async def build_agent_context(
        self,
        agent_id: str,
        execution_id: str,
        current_task: Dict[str, Any],
        memory_config: MemoryConfig,
    ) -> Dict[str, Any]:
        """构建 Agent 的完整上下文

        组合短期记忆（上下文窗口）和长期记忆（知识库检索），返回统一的上下文字典。

        Args:
            agent_id: 智能体ID
            execution_id: 执行实例ID
            current_task: 当前任务信息（需包含 description 字段）
            memory_config: 记忆配置

        Returns:
            包含 short_term_memory / knowledge_base_results 的上下文字典
        """
        context: Dict[str, Any] = {}

        # 短期记忆
        if memory_config.short_term_enabled:
            context["short_term_memory"] = await self.get_context_window(
                execution_id=execution_id,
                window_size=memory_config.short_term_window,
            )

        # 长期记忆（知识库检索）
        if memory_config.long_term_enabled:
            query = current_task.get("description", "")
            if query:
                context["knowledge_base_results"] = await self.retrieve_from_knowledge_base(
                    agent_id=agent_id,
                    query=query,
                    top_k=memory_config.top_k,
                )

        return context

    # ── P1-2: Agent 长期记忆 ────────────────────────────────────

    async def save_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "conclusion",
        importance: float = 1.0,
        execution_id: str = None,
        metadata: dict = None,
    ) -> AgentMemory:
        """保存一条 Agent 记忆到数据库和向量存储。

        Args:
            agent_id: Agent ID
            content: 记忆内容
            memory_type: conclusion/feedback/pattern
            importance: 重要性权重 0-5
            execution_id: 关联执行 ID
            metadata: 额外元数据
        """
        memory = AgentMemory(
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            execution_id=execution_id,
            metadata_=metadata or {},
        )
        self.db.add(memory)
        await self.db.flush()

        # 同时写入向量存储以便语义检索
        try:
            if self.vector_store.is_available():
                await self.vector_store.add_documents(
                    knowledge_base_id=f"memory_{agent_id}",
                    documents=[{
                        "id": f"mem_{memory.id}",
                        "content": content,
                        "metadata": {
                            "agent_id": agent_id,
                            "memory_type": memory_type,
                            "memory_id": str(memory.id),
                            "importance": importance,
                        },
                    }],
                )
        except Exception as e:
            logger.warning(f"Failed to index memory to vector store: {e}")

        return memory

    async def recall_memories(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """召回与查询相关的 Agent 记忆。

        优先使用向量检索（超时5秒），降级到DB查询。

        Args:
            agent_id: Agent ID
            query: 查询文本
            top_k: 返回数量
        """
        import asyncio as _aio
        results = []

        # 向量检索（带超时）
        try:
            if self.vector_store.is_available():
                vs_results = await _aio.wait_for(
                    self.vector_store.search(
                        knowledge_base_id=f"memory_{agent_id}",
                        query=query,
                        top_k=top_k,
                    ),
                    timeout=5,
                )
                if vs_results:
                    for r in vs_results:
                        results.append({
                            "content": r.get("content", ""),
                            "memory_type": r.get("metadata", {}).get("memory_type", "conclusion"),
                            "importance": r.get("metadata", {}).get("importance", 1.0),
                            "distance": r.get("distance", 0),
                        })
        except Exception as e:
            logger.warning(f"Vector recall failed, falling back to DB: {e}")

        # 降级：直接从 DB 取最近记忆
        if not results:
            db_result = await self.db.execute(
                select(AgentMemory)
                .where(AgentMemory.agent_id == agent_id)
                .order_by(AgentMemory.created_at.desc())
                .limit(top_k)
            )
            memories = db_result.scalars().all()
            for m in memories:
                results.append({
                    "content": m.content,
                    "memory_type": m.memory_type,
                    "importance": m.importance,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })

        return results

    # ── 复合评分记忆检索 ───────────────────────────────────

    @staticmethod
    def composite_score(
        recency: float = 1.0,
        semantic: float = 1.0,
        importance: float = 1.0,
        alpha: float = 0.4,
        beta: float = 0.4,
        gamma: float = 0.2,
    ) -> float:
        """三维复合记忆评分

        alpha × recency + beta × semantic + gamma × importance
        默认权重: 时效40% + 语义40% + 重要性20%
        """
        return alpha * recency + beta * semantic + gamma * importance

    async def recall_memories_scored(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5,
        alpha: float = 0.3,
        beta: float = 0.4,
        gamma: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """复合评分记忆召回 — 三维检索（recency + semantic + importance）

        先用向量检索获取候选，再叠加 recency 和 importance 计算最终得分。

        Args:
            agent_id: Agent ID
            query: 查询文本
            top_k: 返回数量
            alpha: recency 权重
            beta: semantic 权重
            gamma: importance 权重
        """
        import asyncio as _aio
        from datetime import datetime, timezone

        # 向量语义检索（取3倍候选）
        candidates = []
        try:
            if self.vector_store.is_available():
                vs_results = await _aio.wait_for(
                    self.vector_store.search(
                        knowledge_base_id=f"memory_{agent_id}",
                        query=query,
                        top_k=top_k * 3,
                    ),
                    timeout=5,
                )
                now = datetime.now(timezone.utc)
                for r in vs_results:
                    # 计算 recency：基于记忆创建时间的指数衰减
                    created_str = r.get("metadata", {}).get("created_at")
                    recency = 1.0  # 默认无衰减
                    if created_str:
                        try:
                            created = datetime.fromisoformat(created_str)
                            age_hours = (now - created).total_seconds() / 3600
                            # 指数衰减：24h半衰期
                            recency = max(0.01, 2 ** (-age_hours / 24))
                        except Exception as e:
                            logger.debug(f"Failed to parse memory timestamp: {e}")

                    candidates.append({
                        "content": r.get("content", ""),
                        "memory_type": r.get("metadata", {}).get("memory_type", "conclusion"),
                        "importance": r.get("metadata", {}).get("importance", 1.0),
                        "scope": r.get("metadata", {}).get("scope", ""),
                        "distance": r.get("distance", 0),
                        "recency": recency,
                    })
        except Exception as e:
            logger.warning(f"Vector recall failed: {e}")

        # 降级：DB 查询
        if not candidates:
            db_result = await self.db.execute(
                select(AgentMemory)
                .where(AgentMemory.agent_id == agent_id)
                .order_by(AgentMemory.importance.desc(), AgentMemory.recency_weight.desc(), AgentMemory.created_at.desc())
                .limit(top_k * 2)
            )
            now = datetime.now(timezone.utc)
            for m in db_result.scalars().all():
                age_hours = (now - (m.created_at or now)).total_seconds() / 3600
                candidates.append({
                    "content": m.content,
                    "memory_type": m.memory_type,
                    "importance": m.importance,
                    "recency": max(0.01, 2 ** (-age_hours / 24)),
                    "distance": 0.0,
                })

        # 计算复合得分
        max_dist = max((c["distance"] for c in candidates), default=1.0)
        for c in candidates:
            semantic = 1.0 - (c["distance"] / max_dist) if max_dist > 0 else 1.0
            c["_score"] = self.composite_score(
                recency=c["recency"],
                semantic=semantic,
                importance=c["importance"],
                alpha=alpha, beta=beta, gamma=gamma,
            )

        # 排序返回
        candidates.sort(key=lambda c: c["_score"], reverse=True)
        return candidates[:top_k]

    # ── Scope-based 记忆管理 ───────────────────────────────

    @staticmethod
    def build_scope(crew_id: str, level: str, entity_id: str = None) -> str:
        """构建路径式scope。

        Args:
            crew_id: Crew/项目ID
            level: agent, task, shared
            entity_id: 实体ID（agent_id或task_id）

        Returns:
            scope路径: /project/{crew_id}/{level}/{entity_id}
        """
        if level == "shared":
            return f"/project/{crew_id}/shared"
        return f"/project/{crew_id}/{level}/{entity_id}"

    async def save_memory_scoped(
        self,
        agent_id: str,
        content: str,
        scope: str,
        memory_type: str = "conclusion",
        importance: float = 1.0,
        execution_id: str = None,
        metadata: dict = None,
    ) -> AgentMemory:
        """保存带scope的Agent记忆。

        Args:
            agent_id: Agent ID
            content: 记忆内容
            scope: scope路径，如 /project/{crew_id}/agent/{agent_id}
            memory_type: conclusion/feedback/pattern
            importance: 重要性 0-5
            execution_id: 关联执行ID
            metadata: 额外元数据
        """
        memory = AgentMemory(
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            scope=scope,
            execution_id=execution_id,
            metadata_=metadata or {},
        )
        self.db.add(memory)
        await self.db.flush()

        # 向量索引（带scope标签）
        try:
            if self.vector_store.is_available():
                await self.vector_store.add_documents(
                    knowledge_base_id=f"scoped_memory_{agent_id}",
                    documents=[{
                        "id": f"mem_scoped_{memory.id}",
                        "content": content,
                        "metadata": {
                            "agent_id": agent_id,
                            "memory_type": memory_type,
                            "memory_id": str(memory.id),
                            "scope": scope,
                            "importance": importance,
                        },
                    }],
                )
        except Exception as e:
            logger.warning(f"Failed to index scoped memory: {e}")

        return memory

    async def recall_by_scope(
        self,
        scope: str,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """按scope检索记忆。

        Args:
            scope: scope路径（支持前缀匹配，如 /project/{crew_id}/ 获取项目下所有记忆）
            top_k: 返回数量
        """
        result = await self.db.execute(
            select(AgentMemory)
            .where(AgentMemory.scope.like(f"{scope}%"))
            .order_by(AgentMemory.importance.desc(), AgentMemory.created_at.desc())
            .limit(top_k)
        )
        memories = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "content": m.content,
                "memory_type": m.memory_type,
                "importance": m.importance,
                "scope": m.scope,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memories
        ]

    async def forget_by_scope(self, scope: str) -> int:
        """删除指定scope下的记忆。

        Args:
            scope: scope路径（精确匹配或前缀匹配）

        Returns:
            删除的记忆数量
        """
        # scope 以 / 结尾 → 前缀匹配；否则精确匹配
        if scope.endswith("/"):
            result = await self.db.execute(
                select(AgentMemory).where(AgentMemory.scope.like(f"{scope}%"))
            )
        else:
            result = await self.db.execute(
                select(AgentMemory).where(AgentMemory.scope == scope)
            )
        memories = result.scalars().all()
        for m in memories:
            await self.db.delete(m)
        return len(memories)

    async def memory_tree(self, crew_id: str) -> Dict[str, Any]:
        """查看项目的scope树结构。

        Args:
            crew_id: 项目/工作流ID

        Returns:
            scope树结构，统计每个scope下的记忆数量
        """
        result = await self.db.execute(
            select(AgentMemory).where(
                AgentMemory.scope.like(f"/project/{crew_id}/%")
            )
        )
        memories = result.scalars().all()

        tree: Dict[str, Any] = {
            "project_id": crew_id,
            "scopes": {},
            "total_memories": len(memories),
        }

        for m in memories:
            scope = m.scope or f"/project/{crew_id}/unscoped"
            if scope not in tree["scopes"]:
                tree["scopes"][scope] = {"count": 0, "types": {}}
            tree["scopes"][scope]["count"] += 1
            mem_type = m.memory_type or "unknown"
            tree["scopes"][scope]["types"][mem_type] = \
                tree["scopes"][scope]["types"].get(mem_type, 0) + 1

        return tree
