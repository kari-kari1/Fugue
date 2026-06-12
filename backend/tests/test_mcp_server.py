"""MCP Server 基础结构测试

验证 MCP Server 正确注册了 tools、resources、prompts。
"""

import pytest
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def server():
    """Module-level server fixture (shared by all test classes)."""
    from app.mcp_server.server import create_mcp_server
    return create_mcp_server()


class TestMCPServerFactory:
    """测试 MCP Server 工厂函数"""

    def test_create_mcp_server_returns_fastmcp_instance(self):
        """create_mcp_server 应返回 FastMCP 实例"""
        from app.mcp_server.server import create_mcp_server

        server = create_mcp_server()
        assert isinstance(server, FastMCP)
        assert server.name == "Fugue"

    def test_mcp_server_has_list_methods(self):
        """FastMCP 实例应具备 list_tools / list_resources / list_prompts 方法"""
        from app.mcp_server.server import create_mcp_server

        server = create_mcp_server()
        assert hasattr(server, "list_tools")
        assert hasattr(server, "list_resources")
        assert hasattr(server, "list_prompts")

    def test_get_mcp_server_returns_singleton(self):
        """get_mcp_server 应返回同一实例（单例模式）"""
        from app.mcp_server.server import get_mcp_server, _reset_server

        _reset_server()
        s1 = get_mcp_server()
        s2 = get_mcp_server()
        assert s1 is s2
        _reset_server()


class TestMCPTools:
    """测试 MCP Tools 注册"""

    @pytest.mark.asyncio
    async def test_mcp_server_has_execute_workflow_tool(self, server):
        """应注册 execute_workflow 工具"""
        tools = await server.list_tools()
        tool_names = [t.name for t in tools]
        assert "execute_workflow" in tool_names

    @pytest.mark.asyncio
    async def test_mcp_server_has_get_execution_status_tool(self, server):
        """应注册 get_execution_status 工具"""
        tools = await server.list_tools()
        tool_names = [t.name for t in tools]
        assert "get_execution_status" in tool_names

    @pytest.mark.asyncio
    async def test_mcp_server_has_list_workflows_tool(self, server):
        """应注册 list_workflows 工具"""
        tools = await server.list_tools()
        tool_names = [t.name for t in tools]
        assert "list_workflows" in tool_names

    @pytest.mark.asyncio
    async def test_mcp_server_has_all_agent_tools(self, server):
        """应包含全部三个 Agent 工具"""
        tools = await server.list_tools()
        tool_names = {t.name for t in tools}
        expected = {"execute_workflow", "get_execution_status", "list_workflows"}
        assert expected.issubset(tool_names)

    @pytest.mark.asyncio
    async def test_execute_workflow_tool_has_description(self, server):
        """execute_workflow 工具应有描述"""
        tools = await server.list_tools()
        tool = next(t for t in tools if t.name == "execute_workflow")
        assert tool.description is not None
        assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_list_workflows_tool_has_input_schema(self, server):
        """list_workflows 工具应有输入 schema（limit/offset 参数）"""
        tools = await server.list_tools()
        tool = next(t for t in tools if t.name == "list_workflows")
        props = tool.inputSchema.get("properties", {})
        assert "limit" in props or "offset" in props


class TestMCPResources:
    """测试 MCP Resources 注册"""

    @pytest.mark.asyncio
    async def test_mcp_server_has_workflow_list_resource(self, server):
        """应注册 fugue://workflows 资源"""
        resources = await server.list_resources()
        uris = [str(r.uri) for r in resources]
        assert any("fugue://workflows" in u for u in uris)

    @pytest.mark.asyncio
    async def test_mcp_server_has_resource_templates(self, server):
        """应注册资源模板（包含 workflow_id 参数）"""
        templates = await server.list_resource_templates()
        assert len(templates) > 0
        template_uris = [str(t.uriTemplate) for t in templates]
        assert any("workflow" in u.lower() for u in template_uris)


class TestMCPPrompts:
    """测试 MCP Prompts 注册"""

    @pytest.mark.asyncio
    async def test_mcp_server_has_workflow_analysis_prompt(self, server):
        """应注册 workflow_analysis 提示词"""
        prompts = await server.list_prompts()
        prompt_names = [p.name for p in prompts]
        assert "workflow_analysis" in prompt_names

    @pytest.mark.asyncio
    async def test_mcp_server_has_agent_optimization_prompt(self, server):
        """应注册 agent_optimization 提示词"""
        prompts = await server.list_prompts()
        prompt_names = [p.name for p in prompts]
        assert "agent_optimization" in prompt_names

    @pytest.mark.asyncio
    async def test_mcp_server_has_execution_debugging_prompt(self, server):
        """应注册 execution_debugging 提示词"""
        prompts = await server.list_prompts()
        prompt_names = [p.name for p in prompts]
        assert "execution_debugging" in prompt_names

    @pytest.mark.asyncio
    async def test_mcp_server_has_all_prompts(self, server):
        """应包含全部三个提示词模板"""
        prompts = await server.list_prompts()
        prompt_names = {p.name for p in prompts}
        expected = {"workflow_analysis", "agent_optimization", "execution_debugging"}
        assert expected.issubset(prompt_names)

    @pytest.mark.asyncio
    async def test_workflow_analysis_prompt_has_arguments(self, server):
        """workflow_analysis 应接受 workflow_name 和 workflow_description 参数"""
        prompts = await server.list_prompts()
        prompt = next(p for p in prompts if p.name == "workflow_analysis")
        arg_names = {a.name for a in prompt.arguments}
        assert "workflow_name" in arg_names
        assert "workflow_description" in arg_names
