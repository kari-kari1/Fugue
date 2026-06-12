"""审批管理器 — 三层级审批模式（safe / semi_auto / full_auto）

控制工具执行前是否需要人工审批，基于工具风险等级与审批模式的组合决策。
使用 asyncio.Event 实现异步等待/通知模式。
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ApprovalMode(str, Enum):
    """审批模式枚举"""
    SAFE = "safe"           # 所有操作均需审批
    SEMI_AUTO = "semi_auto" # 中等/低风险自动通过，高/临界需审批
    FULL_AUTO = "full_auto" # 所有操作均自动通过


class ToolRiskLevel(str, Enum):
    """工具风险等级枚举"""
    LOW = "low"           # file_read, web_search
    MEDIUM = "medium"     # file_write, api_call
    HIGH = "high"         # shell_execute, database_query
    CRITICAL = "critical" # destructive ops: delete_database, drop_table


class ApprovalStatus(str, Enum):
    """审批状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


# 默认工具风险等级映射
_DEFAULT_TOOL_RISK_LEVELS: Dict[str, ToolRiskLevel] = {
    # 低风险 — 只读、查询类
    "file_read": ToolRiskLevel.LOW,
    "web_search": ToolRiskLevel.LOW,
    "get_execution_status": ToolRiskLevel.LOW,
    "list_workflows": ToolRiskLevel.LOW,
    "read_page": ToolRiskLevel.LOW,
    # 中等风险 — 写入、外部调用
    "file_write": ToolRiskLevel.MEDIUM,
    "api_call": ToolRiskLevel.MEDIUM,
    "execute_workflow": ToolRiskLevel.MEDIUM,
    "send_message": ToolRiskLevel.MEDIUM,
    # 高风险 — 系统命令、数据库操作
    "shell_execute": ToolRiskLevel.HIGH,
    "database_query": ToolRiskLevel.HIGH,
    # 临界风险 — 破坏性操作
    "delete_database": ToolRiskLevel.CRITICAL,
    "drop_table": ToolRiskLevel.CRITICAL,
}


class ApprovalManager:
    """审批管理器

    管理工具执行的审批流程，支持三种审批模式。
    使用内存存储和 asyncio.Event 实现等待/通知。
    """

    def __init__(self) -> None:
        self._requests: Dict[str, Dict[str, Any]] = {}
        self._events: Dict[str, asyncio.Event] = {}
        self._tool_risk_levels: Dict[str, ToolRiskLevel] = dict(
            _DEFAULT_TOOL_RISK_LEVELS
        )

    def get_tool_risk_level(self, tool_name: str) -> ToolRiskLevel:
        """获取工具的风险等级，未映射的默认为MEDIUM"""
        return self._tool_risk_levels.get(tool_name, ToolRiskLevel.MEDIUM)

    def requires_approval(
        self,
        mode: ApprovalMode,
        tool_name: str,
        risk_level: Optional[ToolRiskLevel] = None,
    ) -> bool:
        """判断工具执行是否需要审批

        Args:
            mode: 当前审批模式
            tool_name: 工具名称
            risk_level: 可选显式风险等级，覆盖工具映射

        Returns:
            True 表示需要人工审批，False 表示自动通过
        """
        if risk_level is None:
            risk_level = self.get_tool_risk_level(tool_name)

        if mode == ApprovalMode.SAFE:
            return True
        elif mode == ApprovalMode.FULL_AUTO:
            return False
        else:
            # SEMI_AUTO: HIGH和CRITICAL需要审批
            return risk_level in (ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL)

    async def create_approval_request(
        self,
        execution_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        risk_level: Optional[ToolRiskLevel] = None,
    ) -> Dict[str, Any]:
        """创建审批请求

        Args:
            execution_id: 执行ID
            tool_name: 工具名称
            tool_args: 工具参数
            risk_level: 风险等级（可选，默认从工具映射获取）

        Returns:
            审批请求字典
        """
        request_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        if risk_level is None:
            risk_level = self.get_tool_risk_level(tool_name)

        request = {
            "request_id": request_id,
            "execution_id": execution_id,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "risk_level": risk_level,
            "status": ApprovalStatus.PENDING,
            "approved_by": None,
            "approved_at": None,
            "rejected_at": None,
            "reject_reason": None,
            "created_at": now,
        }

        self._requests[request_id] = request
        self._events[request_id] = asyncio.Event()

        logger.info(
            f"Created approval request {request_id} for tool '{tool_name}' "
            f"(risk={risk_level.value}, execution={execution_id})"
        )
        return dict(request)

    async def approve_request(
        self,
        request_id: str,
        approved_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """批准审批请求

        Args:
            request_id: 请求ID
            approved_by: 审批人标识

        Returns:
            更新后的审批请求

        Raises:
            KeyError: 请求ID不存在
            ValueError: 请求已处理（非pending状态）
        """
        if request_id not in self._requests:
            raise KeyError(f"request_id '{request_id}' not found")

        request = self._requests[request_id]
        if request["status"] != ApprovalStatus.PENDING:
            raise ValueError(
                f"Request '{request_id}' already {request['status'].value}"
            )

        now = datetime.now(timezone.utc)
        request["status"] = ApprovalStatus.APPROVED
        request["approved_by"] = approved_by
        request["approved_at"] = now

        # 通知等待者
        event = self._events.get(request_id)
        if event:
            event.set()

        logger.info(f"Approved request {request_id} by {approved_by or 'system'}")
        return dict(request)

    async def reject_request(
        self,
        request_id: str,
        reason: str = "",
    ) -> Dict[str, Any]:
        """拒绝审批请求

        Args:
            request_id: 请求ID
            reason: 拒绝原因

        Returns:
            更新后的审批请求

        Raises:
            KeyError: 请求ID不存在
            ValueError: 请求已处理（非pending状态）
        """
        if request_id not in self._requests:
            raise KeyError(f"request_id '{request_id}' not found")

        request = self._requests[request_id]
        if request["status"] != ApprovalStatus.PENDING:
            raise ValueError(
                f"Request '{request_id}' already {request['status'].value}"
            )

        now = datetime.now(timezone.utc)
        request["status"] = ApprovalStatus.REJECTED
        request["rejected_at"] = now
        request["reject_reason"] = reason

        # 通知等待者
        event = self._events.get(request_id)
        if event:
            event.set()

        logger.info(f"Rejected request {request_id}: {reason}")
        return dict(request)

    async def wait_for_approval(
        self,
        request_id: str,
        timeout: float = 300,
    ) -> Dict[str, Any]:
        """等待审批结果

        使用 asyncio.Event 实现等待/通知模式。

        Args:
            request_id: 请求ID
            timeout: 超时时间（秒），默认5分钟

        Returns:
            审批请求结果
        """
        request = self._requests.get(request_id)
        if not request:
            raise KeyError(f"request_id '{request_id}' not found")

        # 如果已处理，直接返回
        if request["status"] != ApprovalStatus.PENDING:
            return dict(request)

        event = self._events.get(request_id)
        if not event:
            event = asyncio.Event()
            self._events[request_id] = event

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            request["status"] = ApprovalStatus.TIMEOUT
            logger.warning(f"Approval request {request_id} timed out after {timeout}s")

        return dict(request)

    def get_pending_requests(
        self,
        execution_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取待审批请求列表

        Args:
            execution_id: 可选，按执行ID过滤

        Returns:
            待审批请求列表
        """
        results = []
        for req in self._requests.values():
            if req["status"] != ApprovalStatus.PENDING:
                continue
            if execution_id and req["execution_id"] != execution_id:
                continue
            results.append(dict(req))
        return results


# 全局单例
_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """获取审批管理器全局单例"""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager
