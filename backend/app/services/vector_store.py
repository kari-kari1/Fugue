"""向量存储服务（基于 ChromaDB）— A3+A4: 本地化 + 开关 + 懒加载"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局单例（延迟加载）
_embedding_model = None
_vector_store: Optional['VectorStoreService'] = None


def get_embedding_model():
    """获取 Embedding 模型单例（懒加载）"""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SentenceTransformer model (this may take a moment)...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def get_vector_store() -> Optional['VectorStoreService']:
    """获取 VectorStoreService 单例（A4: 受 USE_VECTOR_STORE 控制）"""
    if not settings.USE_VECTOR_STORE:
        return None
    global _vector_store
    if _vector_store is None:
        try:
            _vector_store = VectorStoreService()
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning("ChromaDB not available, vector store disabled: %s", e)
            return None
        except Exception as e:
            logger.warning("Failed to initialize vector store: %s", e)
            return None
    return _vector_store


class VectorStoreService:
    """向量存储服务"""

    def __init__(self):
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        self._available = True
        try:
            chroma_path = str(Path.home() / ".fugue" / "chromadb")
            Path(chroma_path).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=chroma_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info(f"ChromaDB PersistentClient initialized at {chroma_path}")
        except Exception as e:
            self._available = False
            self.client = None
            logger.warning(f"ChromaDB not available, vector store disabled: {e}")

    def is_available(self) -> bool:
        """检查向量存储是否可用"""
        return self._available and self.client is not None

    async def create_collection(self, knowledge_base_id: str) -> Any:
        """创建向量集合"""
        collection_name = f"kb_{knowledge_base_id}"
        logger.info("Creating ChromaDB collection: %s", collection_name)
        return await asyncio.to_thread(
            self.client.get_or_create_collection,
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def get_collection(self, knowledge_base_id: str) -> Any:
        """获取向量集合"""
        return await asyncio.to_thread(
            self.client.get_collection,
            name=f"kb_{knowledge_base_id}",
        )

    async def add_documents(
        self,
        knowledge_base_id: str,
        documents: List[Dict[str, Any]],
    ):
        """添加文档到向量库

        Args:
            knowledge_base_id: 知识库ID
            documents: 文档列表，每个文档包含 id, content, metadata
        """
        if not documents:
            return

        collection = await self.get_collection(knowledge_base_id)
        model = get_embedding_model()

        texts = [doc["content"] for doc in documents]
        embeddings = await asyncio.to_thread(model.encode, texts)
        embeddings = embeddings.tolist()
        ids = [doc["id"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        await asyncio.to_thread(
            collection.add,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info("Added %d documents to collection kb_%s", len(documents), knowledge_base_id)

    async def search(
        self,
        knowledge_base_id: str,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索相似文档

        Args:
            knowledge_base_id: 知识库ID
            query: 查询文本
            top_k: 返回结果数量
            filters: ChromaDB where 过滤条件

        Returns:
            匹配结果列表，每项包含 id, content, metadata, distance
        """
        collection = await self.get_collection(knowledge_base_id)
        model = get_embedding_model()

        query_embedding = await asyncio.to_thread(model.encode, query)
        query_embedding = query_embedding.tolist()

        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
        }
        if filters:
            kwargs["where"] = filters

        results = await asyncio.to_thread(collection.query, **kwargs)

        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            })
        return items

    async def delete_documents(
        self,
        knowledge_base_id: str,
        document_ids: List[str],
    ):
        """删除向量库中的文档"""
        if not document_ids:
            return
        collection = await self.get_collection(knowledge_base_id)
        await asyncio.to_thread(collection.delete, ids=document_ids)
        logger.info("Deleted %d documents from collection kb_%s", len(document_ids), knowledge_base_id)

    async def delete_collection(self, knowledge_base_id: str):
        """删除整个向量集合"""
        collection_name = f"kb_{knowledge_base_id}"
        logger.info("Deleting ChromaDB collection: %s", collection_name)
        await asyncio.to_thread(
            self.client.delete_collection,
            name=collection_name,
        )

    async def get_collection_stats(self, knowledge_base_id: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        collection = await self.get_collection(knowledge_base_id)
        count = await asyncio.to_thread(collection.count)
        return {
            "count": count,
            "name": collection.name,
        }

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
        """将文本按指定大小分块，支持重叠"""
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - chunk_overlap
        return chunks

    @staticmethod
    def bm25_score(query: str, documents: list[str]) -> list[float]:
        """简化 BM25 关键词匹配评分

        对每个文档计算查询词频加权得分，不使用 IDF 简化（适合小规模检索）。
        """
        import re
        query_terms = set(re.findall(r'\w+', query.lower()))
        if not query_terms:
            return [0.0] * len(documents)
        scores = []
        for doc in documents:
            doc_lower = doc.lower()
            score = sum(1.0 for t in query_terms if t in doc_lower)
            # 归一化：除以文档长度防止长文档优势
            doc_len = max(len(doc_lower.split()), 1)
            scores.append(score / doc_len * 100)
        return scores

    async def hybrid_search(
        self,
        knowledge_base_id: str,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        filters: Dict[str, Any] = None,
    ) -> list[Dict[str, Any]]:
        """混合检索：向量语义 + BM25 关键词，加权合并

        Args:
            knowledge_base_id: 知识库ID
            query: 查询文本
            top_k: 返回结果数
            semantic_weight: 语义权重 (0-1)，剩余为BM25权重
            filters: 过滤条件
        """
        # 1) 向量语义检索（取2倍候选）
        vector_results = await self.search(
            knowledge_base_id=knowledge_base_id,
            query=query,
            top_k=top_k * 2,
            filters=filters,
        )
        if not vector_results:
            return []

        # 2) BM25 关键词评分
        docs_for_bm25 = [r["content"] for r in vector_results]
        bm25_scores = self.bm25_score(query, docs_for_bm25)

        # 3) 合并评分：语义距离归一化 + BM25 归一化
        max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0
        max_dist = max(r.get("distance", 0) for r in vector_results) or 1.0

        for i, r in enumerate(vector_results):
            # 向量距离归一化为相似度 (1 - distance/max_dist)
            dist = r.get("distance", 0)
            semantic_sim = 1.0 - (dist / max_dist) if max_dist > 0 else 1.0
            keyword_sim = bm25_scores[i] / max_bm25 if max_bm25 > 0 else 0.0
            r["_score"] = semantic_weight * semantic_sim + (1 - semantic_weight) * keyword_sim
            r["_semantic"] = semantic_sim
            r["_keyword"] = keyword_sim

        # 4) 按综合得分重排序
        vector_results.sort(key=lambda r: r["_score"], reverse=True)
        return vector_results[:top_k]
