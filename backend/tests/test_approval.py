"""审批模式三层级单元测试"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.services.approval_manager import (
    ApprovalManager,
    ApprovalMode,
    ApprovalStatus,
    ToolRiskLevel,
    get_approval_manager,
)


# ── 工具风险等级分类测试 ──────────────────────────────────────


class TestToolRiskClassification:
    """验证工具名称到风险等级的正确映射"""

    def test_low_risk_tools(self):
        """file_read、web_search属于低风险"""
        manager = ApprovalManager()
        assert manager.get_tool_risk_level("file_read") == ToolRiskLevel.LOW
        assert manager.get_tool_risk_level("web_search") == ToolRiskLevel.LOW
        assert manager.get_tool_risk_level("list_workflows") == ToolRiskLevel.LOW

    def test_medium_risk_tools(self):
        """file_write、api_call属于中等风险"""
        manager = ApprovalManager()
        assert manager.get_tool_risk_level("file_write") == ToolRiskLevel.MEDIUM
        assert manager.get_tool_risk_level("api_call") == ToolRiskLevel.MEDIUM
        assert manager.get_tool_risk_level("execute_workflow") == ToolRiskLevel.MEDIUM

    def test_high_risk_tools(self):
        """shell_execute、database_query属于高风险"""
        manager = ApprovalManager()
        assert manager.get_tool_risk_level("shell_execute") == ToolRiskLevel.HIGH
        assert manager.get_tool_risk_level("database_query") == ToolRiskLevel.HIGH

    def test_critical_risk_tools(self):
        """rm -rf / DROP TABLE等属于临界风险"""
        manager = ApprovalManager()
        assert manager.get_tool_risk_level("delete_database") == ToolRiskLevel.CRITICAL
        assert manager.get_tool_risk_level("drop_table") == ToolRiskLevel.CRITICAL

    def test_unknown_tool_defaults_to_medium(self):
        """未映射的工具默认为中等风险"""
        manager = ApprovalManager()
        assert manager.get_tool_risk_level("some_unknown_tool") == ToolRiskLevel.MEDIUM


# ── 审批模式决策测试 ──────────────────────────────────────────


class TestApprovalModeDecision:
    """验证三种审批模式下的审批需求决策"""

    def test_safe_mode_requires_all_approvals(self):
        """Safe模式：所有操作均需要审批"""
        manager = ApprovalManager()
        assert manager.requires_approval(ApprovalMode.SAFE, "file_read") is True
        assert manager.requires_approval(ApprovalMode.SAFE, "web_search") is True
        assert manager.requires_approval(ApprovalMode.SAFE, "file_write") is True
        assert manager.requires_approval(ApprovalMode.SAFE, "shell_execute") is True
        assert manager.requires_approval(ApprovalMode.SAFE, "delete_database") is True

    def test_semi_auto_approves_low_risk(self):
        """Semi-auto模式：低风险自动通过"""
        manager = ApprovalManager()
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "file_read") is False
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "web_search") is False
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "list_workflows") is False

    def test_semi_auto_approves_medium_risk(self):
        """Semi-auto模式：中等风险自动通过"""
        manager = ApprovalManager()
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "file_write") is False
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "api_call") is False
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "execute_workflow") is False

    def test_semi_auto_requires_high_risk_approval(self):
        """Semi-auto模式：高风险需要审批"""
        manager = ApprovalManager()
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "shell_execute") is True
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "database_query") is True

    def test_semi_auto_requires_critical_approval(self):
        """Semi-auto模式：临界风险需要审批"""
        manager = ApprovalManager()
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "delete_database") is True
        assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "drop_table") is True

    def test_full_auto_approves_all(self):
        """Full-auto模式：所有操作自动通过"""
        manager = ApprovalManager()
        assert manager.requires_approval(ApprovalMode.FULL_AUTO, "file_read") is False
        assert manager.requires_approval(ApprovalMode.FULL_AUTO, "file_write") is False
        assert manager.requires_approval(ApprovalMode.FULL_AUTO, "shell_execute") is False
        assert manager.requires_approval(ApprovalMode.FULL_AUTO, "delete_database") is False

    def test_explicit_risk_level_overrides_mapping(self):
        """显式传入risk_level应覆盖工具映射"""
        manager = ApprovalManager()
        # file_read默认LOW，显式传入HIGH应覆盖
        assert manager.requires_approval(
            ApprovalMode.SEMI_AUTO, "file_read", risk_level=ToolRiskLevel.HIGH
        ) is True
        # shell_execute默认HIGH，显式传入LOW应覆盖
        assert manager.requires_approval(
            ApprovalMode.SEMI_AUTO, "shell_execute", risk_level=ToolRiskLevel.LOW
        ) is False


# ── 审批请求生命周期测试 ──────────────────────────────────────


class TestApprovalRequestLifecycle:
    """验证审批请求的创建、批准、拒绝流程"""

    @pytest.mark.asyncio
    async def test_create_approval_request(self):
        """创建请求返回pending状态"""
        manager = ApprovalManager()
        result = await manager.create_approval_request(
            execution_id="exec-123",
            tool_name="shell_execute",
            tool_args={"command": "ls -la"},
            risk_level=ToolRiskLevel.HIGH,
        )

        assert result["status"] == ApprovalStatus.PENDING
        assert result["execution_id"] == "exec-123"
        assert result["tool_name"] == "shell_execute"
        assert result["tool_args"] == {"command": "ls -la"}
        assert result["risk_level"] == ToolRiskLevel.HIGH
        assert result["approved_at"] is None
        assert result["rejected_at"] is None
        assert result["reject_reason"] is None
        assert "request_id" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_approve_request(self):
        """批准请求应设置approved_at和approved_by"""
        manager = ApprovalManager()
        req = await manager.create_approval_request(
            execution_id="exec-1",
            tool_name="shell_execute",
            tool_args={"command": "echo hello"},
        )
        request_id = req["request_id"]

        result = await manager.approve_request(request_id, approved_by="admin")

        assert result["status"] == ApprovalStatus.APPROVED
        assert result["approved_at"] is not None
        assert result["approved_by"] == "admin"

    @pytest.mark.asyncio
    async def test_reject_request(self):
        """拒绝请求应设置rejected_at和reject_reason"""
        manager = ApprovalManager()
        req = await manager.create_approval_request(
            execution_id="exec-1",
            tool_name="shell_execute",
            tool_args={"command": "rm -rf /"},
        )
        request_id = req["request_id"]

        result = await manager.reject_request(request_id, reason="不允许危险命令")

        assert result["status"] == ApprovalStatus.REJECTED
        assert result["rejected_at"] is not None
        assert result["reject_reason"] == "不允许危险命令"

    @pytest.mark.asyncio
    async def test_approve_nonexistent_request_raises(self):
        """批准不存在的请求应抛出KeyError"""
        manager = ApprovalManager()
        with pytest.raises(KeyError, match="request_id"):
            await manager.approve_request("nonexistent-id")

    @pytest.mark.asyncio
    async def test_reject_nonexistent_request_raises(self):
        """拒绝不存在的请求应抛出KeyError"""
        manager = ApprovalManager()
        with pytest.raises(KeyError, match="request_id"):
            await manager.reject_request("nonexistent-id")

    @pytest.mark.asyncio
    async def test_approve_already_resolved_raises(self):
        """重复批准应抛出ValueError"""
        manager = ApprovalManager()
        req = await manager.create_approval_request(
            execution_id="exec-1",
            tool_name="shell_execute",
            tool_args={"command": "ls"},
        )
        await manager.approve_request(req["request_id"])

        with pytest.raises(ValueError, match="already"):
            await manager.approve_request(req["request_id"])


# ── 等待/通知模式测试 ─────────────────────────────────────────


class TestWaitForApproval:
    """验证asyncio.Event等待/通知机制"""

    @pytest.mark.asyncio
    async def test_wait_for_approval_resolves_on_approve(self):
        """wait_for_approval在审批后应立即返回"""
        manager = ApprovalManager()
        req = await manager.create_approval_request(
            execution_id="exec-1",
            tool_name="shell_execute",
            tool_args={"command": "echo test"},
        )
        request_id = req["request_id"]

        async def approve_after_delay():
            await asyncio.sleep(0.05)
            await manager.approve_request(request_id, approved_by="admin")

        # 同时启动等待和延迟批准
        task = asyncio.create_task(approve_after_delay())
        result = await manager.wait_for_approval(request_id, timeout=5)
        await task

        assert result["status"] == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_wait_for_approval_resolves_on_reject(self):
        """wait_for_approval在拒绝后应立即返回"""
        manager = ApprovalManager()
        req = await manager.create_approval_request(
            execution_id="exec-1",
            tool_name="shell_execute",
            tool_args={"command": "rm -rf /"},
        )
        request_id = req["request_id"]

        async def reject_after_delay():
            await asyncio.sleep(0.05)
            await manager.reject_request(request_id, reason="危险操作")

        task = asyncio.create_task(reject_after_delay())
        result = await manager.wait_for_approval(request_id, timeout=5)
        await task

        assert result["status"] == ApprovalStatus.REJECTED

    @pytest.mark.asyncio
    async def test_wait_for_approval_timeout(self):
        """wait_for_approval超时后应返回timeout状态"""
        manager = ApprovalManager()
        req = await manager.create_approval_request(
            execution_id="exec-1",
            tool_name="shell_execute",
            tool_args={"command": "sleep 999"},
        )
        request_id = req["request_id"]

        result = await manager.wait_for_approval(request_id, timeout=0.1)

        assert result["status"] == ApprovalStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_wait_for_approval_resolved_immediately(self):
        """已批准的请求，wait_for_approval应立即返回"""
        manager = ApprovalManager()
        req = await manager.create_approval_request(
            execution_id="exec-1",
            tool_name="shell_execute",
            tool_args={"command": "echo test"},
        )
        request_id = req["request_id"]
        await manager.approve_request(request_id)

        result = await manager.wait_for_approval(request_id, timeout=5)

        assert result["status"] == ApprovalStatus.APPROVED


# ── 查询测试 ──────────────────────────────────────────────────


class TestGetPendingRequests:
    """验证pending请求查询"""

    @pytest.mark.asyncio
    async def test_get_pending_requests(self):
        """get_pending_requests应只返回pending状态的请求"""
        manager = ApprovalManager()
        req1 = await manager.create_approval_request(
            execution_id="exec-1", tool_name="shell_execute", tool_args={"cmd": "ls"}
        )
        req2 = await manager.create_approval_request(
            execution_id="exec-1", tool_name="database_query", tool_args={"q": "SELECT 1"}
        )
        req3 = await manager.create_approval_request(
            execution_id="exec-2", tool_name="shell_execute", tool_args={"cmd": "pwd"}
        )

        # 先批准其中一条
        await manager.approve_request(req1["request_id"])

        pending = manager.get_pending_requests()
        assert len(pending) == 2
        assert all(r["status"] == ApprovalStatus.PENDING for r in pending)

    @pytest.mark.asyncio
    async def test_get_pending_requests_by_execution(self):
        """按execution_id过滤pending请求"""
        manager = ApprovalManager()
        await manager.create_approval_request(
            execution_id="exec-1", tool_name="shell_execute", tool_args={"cmd": "ls"}
        )
        await manager.create_approval_request(
            execution_id="exec-2", tool_name="shell_execute", tool_args={"cmd": "pwd"}
        )

        pending = manager.get_pending_requests(execution_id="exec-1")
        assert len(pending) == 1
        assert pending[0]["execution_id"] == "exec-1"


# ── 全局单例测试 ──────────────────────────────────────────────


class TestGlobalSingleton:
    """验证get_approval_manager单例"""

    def test_singleton_returns_same_instance(self):
        """多次调用应返回同一实例"""
        # 重置单例以确保干净状态
        import app.services.approval_manager as mod
        mod._approval_manager = None

        m1 = get_approval_manager()
        m2 = get_approval_manager()
        assert m1 is m2

        # 恢复
        mod._approval_manager = None
