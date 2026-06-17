"""内置工具单元测试"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.engine.tools import (
    ApiCallTool,
    CodeExecuteTool,
    FileReadTool,
    RecallTool,
    RememberTool,
    SearchKnowledgeTool,
    WebSearchTool,
    get_tool,
)

# ── WebSearchTool ──────────────────────────────────

def test_web_search_tool_openai_schema():
    """测试 WebSearchTool 生成有效的 OpenAI schema"""
    tool = WebSearchTool()
    schema = tool.get_openai_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "web_search"
    assert "query" in schema["function"]["parameters"]["required"]


def test_web_search_tool_anthropic_schema():
    """测试 WebSearchTool 生成有效的 Anthropic schema"""
    tool = WebSearchTool()
    schema = tool.get_anthropic_schema()
    assert schema["name"] == "web_search"
    assert "input_schema" in schema
    assert "query" in schema["input_schema"]["required"]


@pytest.mark.asyncio
async def test_web_search_tool_execute_with_mock():
    """测试 WebSearchTool execute 通过 mock 搜索调用"""
    mock_results = [
        {"title": "结果1", "href": "https://example.com/1", "body": "摘要1"},
        {"title": "结果2", "href": "https://example.com/2", "body": "摘要2"},
    ]

    with patch("app.engine.tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = mock_results
        tool = WebSearchTool()
        output = await tool.execute({"query": "测试搜索", "max_results": 3})
        assert "搜索结果" in output
        assert "结果1" in output
        assert "结果2" in output


@pytest.mark.asyncio
async def test_web_search_tool_execute_empty_results():
    """测试 WebSearchTool 无结果时返回正确提示"""
    with patch("app.engine.tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.return_value = []
        tool = WebSearchTool()
        output = await tool.execute({"query": "不存在的搜索"})
        assert "未找到相关结果" in output


# ── FileReadTool ──────────────────────────────────

def test_file_read_tool_schema():
    """测试 FileReadTool 的 schema 包含 file_path 和 encoding"""
    tool = FileReadTool()
    schema = tool.get_openai_schema()
    assert schema["function"]["name"] == "file_read"
    params = schema["function"]["parameters"]["properties"]
    assert "file_path" in params
    assert "encoding" in params
    assert "file_path" in schema["function"]["parameters"]["required"]


# ── 记忆工具存在性 ─────────────────────────────────

def test_remember_tool_exists():
    """验证 remember 工具已注册"""
    tool = get_tool("remember")
    assert tool is not None
    assert isinstance(tool, RememberTool)
    assert tool.category == "memory"
    assert tool.permissions == "safe"


def test_recall_tool_exists():
    """验证 recall 工具已注册"""
    tool = get_tool("recall")
    assert tool is not None
    assert isinstance(tool, RecallTool)
    assert tool.category == "memory"


def test_search_knowledge_tool_exists():
    """验证 search_knowledge 工具已注册"""
    tool = get_tool("search_knowledge")
    assert tool is not None
    assert isinstance(tool, SearchKnowledgeTool)
    assert tool.category == "memory"
    schema = tool.get_openai_schema()
    assert "query" in schema["function"]["parameters"]["required"]


# ── CodeExecuteTool 安全 ──────────────────────────────────

@pytest.mark.asyncio
async def test_code_execute_tool_blocks_dangerous():
    """测试 CodeExecuteTool 阻止 bash 执行"""
    tool = CodeExecuteTool()
    # bash 语言应被明确拒绝
    output = await tool.execute({"language": "bash", "code": "echo hello"})
    assert "bash" in output.lower() or "已禁用" in output or "安全限制" in output


@pytest.mark.asyncio
async def test_code_execute_tool_requires_language():
    """测试 CodeExecuteTool 需要 language 参数"""
    tool = CodeExecuteTool()
    # Python 运行时不保证存在，但 schema 应正确
    schema = tool.get_openai_schema()
    assert "language" in schema["function"]["parameters"]["required"]
    # 验证 enum 中不包含 bash
    lang_enum = schema["function"]["parameters"]["properties"]["language"]["enum"]
    assert "bash" not in lang_enum


# ── ApiCallTool SSRF 防护 ──────────────────────────────

@pytest.mark.asyncio
async def test_api_call_tool_ssrf_protection_loopback():
    """测试 ApiCallTool 阻止访问 loopback 地址"""
    with patch("socket.gethostbyname", return_value="127.0.0.1"):
        tool = ApiCallTool()
        output = await tool.execute({"url": "http://localhost/admin"})
        assert "安全限制" in output or "内部" in output


@pytest.mark.asyncio
async def test_api_call_tool_ssrf_protection_private():
    """测试 ApiCallTool 阻止访问私有网络地址"""
    with patch("socket.gethostbyname", return_value="192.168.1.1"):
        tool = ApiCallTool()
        output = await tool.execute({"url": "http://internal-server/api"})
        assert "安全限制" in output or "内部" in output or "私有" in output


@pytest.mark.asyncio
async def test_api_call_tool_ssrf_protection_link_local():
    """测试 ApiCallTool 阻止访问链路本地地址"""
    with patch("socket.gethostbyname", return_value="169.254.1.1"):
        tool = ApiCallTool()
        output = await tool.execute({"url": "http://link-local/secret"})
        assert "安全限制" in output or "内部" in output


@pytest.mark.asyncio
async def test_api_call_tool_allows_public():
    """测试 ApiCallTool 允许访问公网地址"""
    with patch("socket.gethostbyname", return_value="93.184.216.34"), \
         patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_resp = MagicMock()
        mock_resp.text = "OK"
        mock_resp.status_code = 200
        mock_req.return_value = mock_resp

        tool = ApiCallTool()
        output = await tool.execute({"url": "https://example.com"})
        assert "API响应" in output
        assert "200" in output
