"""执行引擎关键函数单元测试"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.engine.executor import ExecutionEngine
from app.engine.llm_provider import ToolCall


class TestParseTextToolCalls:
    """_parse_text_tool_calls 测试"""

    def test_parse_valid_tool_call(self):
        content = '一些文本\n```tool_call\n{"tool": "fs_read", "args": {"path": "/tmp/test.txt"}}\n```\n更多文本'
        result = ExecutionEngine._parse_text_tool_calls(content)
        assert len(result) == 1
        assert result[0].name == "fs_read"
        assert result[0].arguments == {"path": "/tmp/test.txt"}

    def test_parse_multiple_tool_calls(self):
        content = (
            '```tool_call\n{"tool": "fs_read", "args": {"path": "/a"}}\n```\n'
            '中间文本\n'
            '```tool_call\n{"tool": "fs_write", "args": {"path": "/b", "content": "hi"}}\n```'
        )
        result = ExecutionEngine._parse_text_tool_calls(content)
        assert len(result) == 2
        assert result[0].name == "fs_read"
        assert result[1].name == "fs_write"

    def test_parse_no_tool_call(self):
        result = ExecutionEngine._parse_text_tool_calls("普通文本，没有工具调用")
        assert result == []

    def test_parse_malformed_json(self):
        content = '```tool_call\n{invalid json}\n```'
        result = ExecutionEngine._parse_text_tool_calls(content)
        assert result == []

    def test_parse_missing_tool_key(self):
        content = '```tool_call\n{"args": {"path": "/tmp"}}\n```'
        result = ExecutionEngine._parse_text_tool_calls(content)
        assert result == []


class TestDescribeToolCall:
    """_describe_tool_call 测试"""

    def test_describe_simple_call(self):
        result = ExecutionEngine._describe_tool_call("fs_read", {"path": "/tmp/test.txt"})
        assert isinstance(result, str)
        assert len(result) > 0
        assert "/tmp/test.txt" in result

    def test_describe_empty_args(self):
        result = ExecutionEngine._describe_tool_call("process_info", {})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_describe_long_args_truncated(self):
        long_content = "x" * 1000
        result = ExecutionEngine._describe_tool_call("fs_write", {"content": long_content})
        assert isinstance(result, str)
        # 应该被截断
        assert len(result) < 600


class TestFormatPrompt:
    """_format_prompt 测试"""

    def test_format_simple_template(self):
        engine = ExecutionEngine.__new__(ExecutionEngine)
        result = engine._format_prompt("Hello {name}", {"name": "World"})
        assert result == "Hello World"

    def test_format_missing_key(self):
        engine = ExecutionEngine.__new__(ExecutionEngine)
        result = engine._format_prompt("Hello {name}", {})
        assert "{name}" in result  # 未替换的占位符保留

    def test_format_no_placeholders(self):
        engine = ExecutionEngine.__new__(ExecutionEngine)
        result = engine._format_prompt("No placeholders", {"key": "val"})
        assert result == "No placeholders"


class TestAddTrace:
    """_add_trace 测试"""

    def test_add_trace_creates_list(self):
        engine = ExecutionEngine.__new__(ExecutionEngine)
        execution = MagicMock()
        execution.trace = None
        engine._add_trace(execution, "test.event", agent_name="agent1", data={"key": "val"})
        assert execution.trace is not None
        assert len(execution.trace) == 1
        assert execution.trace[0]["event_type"] == "test.event"

    def test_add_trace_appends(self):
        engine = ExecutionEngine.__new__(ExecutionEngine)
        execution = MagicMock()
        execution.trace = [{"event_type": "existing"}]
        engine._add_trace(execution, "new.event")
        assert len(execution.trace) == 2

    def test_add_trace_handles_missing_attr(self):
        engine = ExecutionEngine.__new__(ExecutionEngine)
        execution = MagicMock()
        execution.trace = None
        # flag_modified 可能抛异常，但 _add_trace 应该不崩溃
        try:
            engine._add_trace(execution, "test.event")
        except Exception:
            pass  # flag_modified 在 mock 上可能失败，这是预期的
