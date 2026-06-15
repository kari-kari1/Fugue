"""P0 功能集成测试

验证 MCP Server、审批管理器、沙箱管理器、Worktree 管理器等 P0 功能协同工作。
集成测试侧重模块间的集成点，而非重复单元测试。
"""

import os
import sys
import pytest
from app.mcp_server.server import get_mcp_server, create_mcp_server
from app.services.worktree_manager import get_worktree_manager
from app.services.approval_manager import get_approval_manager, ApprovalMode
from app.engine.sandbox import get_sandbox_manager, SandboxConfig, SandboxType


@pytest.mark.asyncio
async def test_mcp_server_lists_all_tools():
    """Verify MCP Server registers all expected tools"""
    server = create_mcp_server()  # Fresh instance to avoid singleton pollution
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert "execute_workflow" in tool_names
    assert "get_execution_status" in tool_names
    assert "list_workflows" in tool_names


@pytest.mark.asyncio
async def test_mcp_server_lists_resources():
    """Verify MCP Server has resources registered"""
    server = create_mcp_server()
    resources = await server.list_resources()
    assert len(resources) > 0


@pytest.mark.asyncio
async def test_mcp_server_lists_prompts():
    """Verify MCP Server has prompts registered"""
    server = create_mcp_server()
    prompts = await server.list_prompts()
    prompt_names = {p.name for p in prompts}
    assert "workflow_analysis" in prompt_names
    assert "agent_optimization" in prompt_names
    assert "execution_debugging" in prompt_names


def test_approval_mode_decision_matrix():
    """Verify approval mode decision logic for all modes and risk levels"""
    manager = get_approval_manager()

    # Safe mode: all require approval
    for tool in ["file_read", "file_write", "shell_execute", "database_query"]:
        assert manager.requires_approval(ApprovalMode.SAFE, tool) is True

    # Semi-auto: only HIGH/CRITICAL require approval
    assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "file_read") is False
    assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "file_write") is False
    assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "shell_execute") is True
    assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "database_query") is True

    # Full-auto: none require approval
    for tool in ["file_read", "file_write", "shell_execute", "database_query"]:
        assert manager.requires_approval(ApprovalMode.FULL_AUTO, tool) is False


def test_sandbox_blocks_known_dangerous_commands():
    """Verify sandbox validates against dangerous command patterns"""
    sandbox = get_sandbox_manager()
    config = SandboxConfig()

    dangerous = ["rm -rf /", "rm -rf /*", "dd if=/dev/zero of=/dev/sda", "mkfs.ext4 /dev/sda1"]
    for cmd in dangerous:
        error = sandbox.validate_command(cmd, config)
        assert error is not None, f"Expected '{cmd}' to be blocked"


@pytest.mark.asyncio
async def test_sandbox_executes_safe_command():
    """Verify sandbox can execute a safe command"""
    sandbox = get_sandbox_manager()
    result = await sandbox.execute_in_sandbox(
        command="echo hello",
        workspace=os.environ.get("TEMP", "/tmp"),
        sandbox_type=SandboxType.NONE,
    )
    assert result["success"] is True
    assert "hello" in result["output"]


def test_worktree_manager_singleton():
    """Verify worktree manager singleton works"""
    m1 = get_worktree_manager()
    m2 = get_worktree_manager()
    assert m1 is m2
