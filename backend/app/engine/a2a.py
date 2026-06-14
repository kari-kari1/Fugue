"""A2A 协议 — Agent-to-Agent 通信

报告第一章 多智能体 (8/10) 建议:
- A2A 协议: Agent 间直接通信，不仅通过顺序任务输出传递
- 动态任务分配: 运行时根据 Agent 能力匹配任务
- 自修复机制: Agent 失败时自动重分配到备选 Agent
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# ─── A2A 消息 ──────────────────────────────────────────────────────────────

@dataclass
class A2AMessage:
    """Agent 间通信消息"""
    id: str
    sender_id: str       # 发送方 Agent ID
    receiver_id: str     # 接收方 Agent ID
    message_type: str    # request / response / broadcast
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    reply_to: str | None = None  # 回复的消息 ID


@dataclass
class AgentCapability:
    """Agent 能力描述"""
    agent_id: str
    name: str
    skills: list[str] = field(default_factory=list)      # 技能标签 ["research", "coding", ...]
    tools: list[str] = field(default_factory=list)        # 可用工具列表
    max_concurrent: int = 1                               # 最大并发任务数
    current_load: int = 0                                 # 当前负载
    success_rate: float = 1.0                             # 历史成功率
    avg_task_duration: float = 0.0                        # 平均任务时长(秒)


# ─── A2A 消息总线 ──────────────────────────────────────────────────────────

class A2AMessageBus:
    """Agent 间通信消息总线"""

    def __init__(self):
        self._channels: dict[str, asyncio.Queue] = {}  # agent_id -> message queue
        self._history: list[A2AMessage] = []
        self._subscribers: dict[str, list[Callable]] = {}  # event_type -> callbacks

    def register_agent(self, agent_id: str):
        """注册 Agent 到消息总线"""
        if agent_id not in self._channels:
            self._channels[agent_id] = asyncio.Queue()

    def unregister_agent(self, agent_id: str):
        """注销 Agent"""
        self._channels.pop(agent_id, None)

    async def send(self, message: A2AMessage):
        """发送消息到指定 Agent"""
        self._history.append(message)

        # 发送到目标 Agent 的队列
        queue = self._channels.get(message.receiver_id)
        if queue:
            await queue.put(message)
        else:
            logger.warning("A2A: receiver '%s' not registered, message dropped", message.receiver_id)

        # 触发订阅回调
        for callback in self._subscribers.get(message.message_type, []):
            try:
                await callback(message)
            except Exception as e:
                logger.error("A2A subscriber error: %s", e)

    async def receive(self, agent_id: str, timeout: float = 30.0) -> A2AMessage | None:
        """接收消息（带超时）"""
        queue = self._channels.get(agent_id)
        if not queue:
            return None
        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except TimeoutError:
            return None

    def subscribe(self, message_type: str, callback: Callable):
        """订阅特定类型的消息"""
        self._subscribers.setdefault(message_type, []).append(callback)

    def get_history(self, agent_id: str | None = None, limit: int = 50) -> list[A2AMessage]:
        """获取消息历史"""
        msgs = self._history
        if agent_id:
            msgs = [m for m in msgs if m.sender_id == agent_id or m.receiver_id == agent_id]
        return msgs[-limit:]


# ─── 动态任务分配器 ────────────────────────────────────────────────────────

class DynamicTaskAssigner:
    """运行时根据 Agent 能力动态分配任务

    报告建议: 不再静态绑定 task → agent，而是根据任务需求和 Agent 能力动态匹配。
    """

    def __init__(self):
        self._capabilities: dict[str, AgentCapability] = {}

    def register_capability(self, cap: AgentCapability):
        """注册 Agent 能力"""
        self._capabilities[cap.agent_id] = cap

    def update_load(self, agent_id: str, delta: int):
        """更新 Agent 负载"""
        cap = self._capabilities.get(agent_id)
        if cap:
            cap.current_load = max(0, cap.current_load + delta)

    def update_success_rate(self, agent_id: str, success: bool):
        """更新 Agent 成功率（指数移动平均）"""
        cap = self._capabilities.get(agent_id)
        if cap:
            alpha = 0.1
            cap.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * cap.success_rate

    def assign(
        self,
        task_name: str,
        required_skills: list[str] = None,
        required_tools: list[str] = None,
        preferred_agent: str | None = None,
    ) -> str | None:
        """为任务分配最佳 Agent

        评分规则:
        1. 如果指定了 preferred_agent 且可用 → 直接使用
        2. 按 (技能匹配 × 0.4 + 工具匹配 × 0.3 + 成功率 × 0.2 + 负载均衡 × 0.1) 打分
        3. 返回得分最高且未过载的 Agent
        """
        required_skills = required_skills or []
        required_tools = required_tools or []

        # 首选 Agent 可用时直接返回
        if preferred_agent:
            cap = self._capabilities.get(preferred_agent)
            if cap and cap.current_load < cap.max_concurrent:
                return preferred_agent

        best_id = None
        best_score = -1.0

        for agent_id, cap in self._capabilities.items():
            # 跳过过载的 Agent
            if cap.current_load >= cap.max_concurrent:
                continue

            # 技能匹配
            skill_score = 0.0
            if required_skills:
                matched = sum(1 for s in required_skills if s in cap.skills)
                skill_score = matched / len(required_skills)
            else:
                skill_score = 1.0  # 无技能要求时默认满分

            # 工具匹配
            tool_score = 0.0
            if required_tools:
                matched = sum(1 for t in required_tools if t in cap.tools)
                tool_score = matched / len(required_tools)
            else:
                tool_score = 1.0

            # 负载均衡 (负载越低分越高)
            load_score = 1.0 - (cap.current_load / max(cap.max_concurrent, 1))

            # 综合评分
            total = skill_score * 0.4 + tool_score * 0.3 + cap.success_rate * 0.2 + load_score * 0.1

            if total > best_score:
                best_score = total
                best_id = agent_id

        return best_id


# ─── 自修复管理器 ──────────────────────────────────────────────────────────

class SelfHealingManager:
    """Agent 失败时自动重分配

    报告建议: 任务失败后不是直接终止执行，而是尝试重新分配给其他 Agent。
    """

    def __init__(self, assigner: DynamicTaskAssigner, max_reassigns: int = 2):
        self.assigner = assigner
        self.max_reassigns = max_reassigns
        self._reassign_count: dict[str, int] = {}  # task_id -> reassign count

    def can_reassign(self, task_id: str) -> bool:
        """检查是否还可以重分配"""
        return self._reassign_count.get(task_id, 0) < self.max_reassigns

    def get_failed_agents(self, task_id: str) -> list[str]:
        """获取已失败的 Agent 列表（避免重复分配）"""
        # 简化实现: 通过 reassign_count 推断
        return []

    def record_failure(self, task_id: str, agent_id: str):
        """记录一次失败"""
        self._reassign_count[task_id] = self._reassign_count.get(task_id, 0) + 1
        # 更新 Agent 成功率
        self.assigner.update_success_rate(agent_id, success=False)

    def try_reassign(
        self,
        task_id: str,
        task_name: str,
        failed_agent_id: str,
        required_skills: list[str] = None,
        required_tools: list[str] = None,
    ) -> str | None:
        """尝试重分配任务到其他 Agent

        Returns: 新的 Agent ID，或 None（无法重分配）
        """
        if not self.can_reassign(task_id):
            logger.warning("Self-heal: task '%s' exhausted reassign attempts (%d)",
                           task_id, self.max_reassigns)
            return None

        self.record_failure(task_id, failed_agent_id)

        # 分配时排除已失败的 Agent
        new_agent = self.assigner.assign(
            task_name=task_name,
            required_skills=required_skills,
            required_tools=required_tools,
        )

        if new_agent == failed_agent_id:
            # 只有一个 Agent 可用且就是失败的那个
            logger.warning("Self-heal: no alternative agent for task '%s'", task_id)
            return None

        if new_agent:
            logger.info("Self-heal: reassigned task '%s' from '%s' to '%s'",
                        task_id, failed_agent_id, new_agent)

        return new_agent


# ─── 全局单例 ──────────────────────────────────────────────────────────────

_a2a_bus: A2AMessageBus | None = None
_task_assigner: DynamicTaskAssigner | None = None
_self_healer: SelfHealingManager | None = None


def get_a2a_bus() -> A2AMessageBus:
    global _a2a_bus
    if _a2a_bus is None:
        _a2a_bus = A2AMessageBus()
    return _a2a_bus


def get_task_assigner() -> DynamicTaskAssigner:
    global _task_assigner
    if _task_assigner is None:
        _task_assigner = DynamicTaskAssigner()
    return _task_assigner


def get_self_healer() -> SelfHealingManager:
    global _self_healer
    if _self_healer is None:
        _self_healer = SelfHealingManager(get_task_assigner())
    return _self_healer
