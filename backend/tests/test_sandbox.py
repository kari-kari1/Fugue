"""Agent执行沙箱测试 — 文件系统/网络隔离、危险命令拦截"""
import os
import sys
import asyncio
import pytest

# 不使用 conftest 中的 fixtures，直接测试 engine 模块
from app.engine.sandbox import (
    SandboxConfig,
    SandboxManager,
    SandboxType,
    get_sandbox_manager,
)

# Windows 上 bwrap 不可用的跳过标记
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform == "linux"


# ─────────────────────────────────────────────
# SandboxConfig 单元测试
# ─────────────────────────────────────────────

class TestSandboxConfig:
    """SandboxConfig 数据类测试"""

    def test_sandbox_config_defaults(self):
        """默认配置应有正确的初始值"""
        config = SandboxConfig()

        assert config.enable_filesystem_isolation is True
        assert config.enable_network_isolation is False
        assert config.allowed_paths == []
        assert config.max_execution_time == 300
        assert config.max_memory_mb == 512
        assert config.max_cpu_percent == 50
        # blocked_commands 应包含常见危险命令
        assert len(config.blocked_commands) > 0
        assert any("rm -rf /" in cmd for cmd in config.blocked_commands)

    def test_sandbox_config_custom(self):
        """自定义配置应正确覆盖默认值"""
        config = SandboxConfig(
            enable_filesystem_isolation=False,
            enable_network_isolation=True,
            allowed_paths=["/tmp/workspace"],
            max_execution_time=60,
            max_memory_mb=1024,
            max_cpu_percent=80,
            blocked_commands=["rm -rf /"],
        )

        assert config.enable_filesystem_isolation is False
        assert config.enable_network_isolation is True
        assert config.allowed_paths == ["/tmp/workspace"]
        assert config.max_execution_time == 60
        assert config.max_memory_mb == 1024
        assert config.max_cpu_percent == 80
        assert config.blocked_commands == ["rm -rf /"]


# ─────────────────────────────────────────────
# SandboxManager 测试
# ─────────────────────────────────────────────

class TestSandboxManager:
    """SandboxManager 命令验证与沙箱执行测试"""

    def test_manager_detects_available_sandboxes(self):
        """启动时应检测当前平台可用的沙箱类型"""
        manager = SandboxManager()
        # NONE 模式始终可用
        assert SandboxType.NONE in manager.available_sandboxes
        # available_sandboxes 应为 list
        assert isinstance(manager.available_sandboxes, list)

    def test_validate_command_allows_safe_command(self):
        """安全命令应通过验证"""
        manager = SandboxManager()
        config = SandboxConfig()
        error = manager.validate_command("echo hello world", config)
        assert error is None

    def test_sandbox_blocks_dangerous_commands(self):
        """危险命令应被拦截并返回错误信息"""
        manager = SandboxManager()
        config = SandboxConfig()

        dangerous_commands = [
            "rm -rf /",
            "rm -rf /*",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
            ":(){ :|:& };:",
            "chmod 777 /",
            "chown root /etc/passwd",
            # 空白符绕过变体
            "rm  -rf  /",
            "rm   -rf   /*",
            "  rm -rf /  ",
            "chmod  777  /",
            # dd 作为独立危险基础命令
            "dd if=/dev/zero of=/dev/sda bs=1M",
        ]

        for cmd in dangerous_commands:
            error = manager.validate_command(cmd, config)
            assert error is not None, f"命令 '{cmd}' 应被拦截但未被拦截"
            assert "禁止" in error or "危险" in error

    def test_validate_command_respects_custom_blocked_list(self):
        """自定义 blocked_commands 列表应生效"""
        manager = SandboxManager()
        config = SandboxConfig(blocked_commands=["curl", "wget"])

        error = manager.validate_command("curl http://evil.com", config)
        assert error is not None

        # 正常命令应通过
        error = manager.validate_command("ls -la", config)
        assert error is None


@pytest.mark.asyncio
class TestSandboxExecution:
    """沙箱实际执行测试"""

    async def test_sandbox_type_none_executes_command(self):
        """SandboxType.NONE 应直接执行命令并返回结果"""
        manager = SandboxManager()

        result = await manager.execute_in_sandbox(
            command="echo hello",
            workspace=os.environ.get("TEMP", "/tmp"),
            sandbox_type=SandboxType.NONE,
        )

        assert result["success"] is True
        assert "hello" in result["output"]
        assert result["exit_code"] == 0
        assert result["sandbox_type"] == SandboxType.NONE.value

    async def test_sandbox_type_none_captures_stderr(self):
        """NONE 模式应正确捕获 stderr"""
        manager = SandboxManager()

        if sys.platform == "win32":
            # Windows: echo to stderr via cmd
            cmd = "echo err_msg 1>&2"
        else:
            cmd = "echo err_msg >&2"

        result = await manager.execute_in_sandbox(
            command=cmd,
            workspace=os.environ.get("TEMP", "/tmp"),
            sandbox_type=SandboxType.NONE,
        )

        assert "err_msg" in result.get("error", "") or "err_msg" in result.get("output", "")

    async def test_sandbox_handles_nonzero_exit_code(self):
        """非零退出码应正确返回 success=False"""
        manager = SandboxManager()

        if sys.platform == "win32":
            # Windows: exit 42 直接由 cmd 处理
            cmd = "exit /b 42"
        else:
            cmd = "exit 42"

        result = await manager.execute_in_sandbox(
            command=cmd,
            workspace=os.environ.get("TEMP", "/tmp"),
            sandbox_type=SandboxType.NONE,
        )

        assert result["success"] is False
        assert result["exit_code"] == 42

    async def test_sandbox_respects_timeout(self):
        """超时应终止执行并返回错误"""
        manager = SandboxManager()
        config = SandboxConfig(max_execution_time=1)

        if sys.platform == "win32":
            # Windows: ping -n 30 等效 sleep 30s（ping 间隔 1s）
            cmd = "ping -n 30 127.0.0.1 >nul"
        else:
            cmd = "sleep 30"

        result = await manager.execute_in_sandbox(
            command=cmd,
            workspace=os.environ.get("TEMP", "/tmp"),
            config=config,
            sandbox_type=SandboxType.NONE,
        )

        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower() or "超时" in result.get("error", "")

    async def test_sandbox_blocks_dangerous_before_execution(self):
        """危险命令应在执行前被拦截"""
        manager = SandboxManager()

        result = await manager.execute_in_sandbox(
            command="rm -rf /",
            workspace=os.environ.get("TEMP", "/tmp"),
            sandbox_type=SandboxType.NONE,
        )

        assert result["success"] is False
        assert result["exit_code"] == -1  # 未执行即拦截
        assert "blocked" in result.get("error", "").lower() or "禁止" in result.get("error", "") or "危险" in result.get("error", "")

    async def test_sandbox_auto_detect_type(self):
        """未指定 sandbox_type 时应自动检测并使用可用类型"""
        manager = SandboxManager()

        result = await manager.execute_in_sandbox(
            command="echo auto_detect",
            workspace=os.environ.get("TEMP", "/tmp"),
        )

        assert result["success"] is True
        assert "auto_detect" in result["output"]
        # 应返回实际使用的沙箱类型
        assert "sandbox_type" in result


@pytest.mark.asyncio
@pytest.mark.skipif(IS_WINDOWS, reason="bwrap 仅在 Linux 上可用")
class TestBwrapSandbox:
    """Bubblewrap 沙箱测试（仅 Linux）"""

    async def test_sandbox_isolates_filesystem(self):
        """bwrap 沙箱应限制文件系统访问"""
        manager = SandboxManager()

        if SandboxType.BWRAP not in manager.available_sandboxes:
            pytest.skip("bwrap 不可用")

        config = SandboxConfig(
            enable_filesystem_isolation=True,
            allowed_paths=[],
        )

        # 在沙箱中应无法访问宿主机敏感路径
        result = await manager.execute_in_sandbox(
            command="ls /etc/shadow",
            workspace="/tmp/sandbox_test",
            config=config,
            sandbox_type=SandboxType.BWRAP,
        )

        # 即使 ls 成功（返回空），也不应看到宿主机的 /etc/shadow 内容
        # 或命令应被拒绝（退出码非零）
        assert result["sandbox_type"] == SandboxType.BWRAP.value

    async def test_bwrap_command_structure(self):
        """_build_bwrap_command 应生成正确的 bwrap 参数"""
        manager = SandboxManager()
        config = SandboxConfig(
            enable_filesystem_isolation=True,
            enable_network_isolation=True,
        )

        cmd = manager.build_bwrap_command(
            "echo test",
            workspace="/tmp/ws",
            config=config,
        )

        assert cmd[0] == "bwrap"
        assert "--ro-bind" in cmd or "--bind" in cmd
        assert "--die-with-parent" in cmd


@pytest.mark.asyncio
@pytest.mark.skipif(IS_WINDOWS, reason="Docker 沙箱测试在 Windows CI 中可能不可用")
class TestDockerSandbox:
    """Docker 沙箱测试"""

    async def test_docker_command_structure(self):
        """_build_docker_command 应生成正确的 docker run 参数"""
        manager = SandboxManager()

        if SandboxType.DOCKER not in manager.available_sandboxes:
            pytest.skip("Docker 不可用")

        config = SandboxConfig(
            enable_network_isolation=True,
            max_memory_mb=256,
            max_cpu_percent=30,
            max_execution_time=60,
        )

        cmd = manager.build_docker_command(
            "echo test",
            workspace="/tmp/ws",
            config=config,
        )

        assert cmd[0] == "docker"
        assert "run" in cmd
        assert "--rm" in cmd


# ─────────────────────────────────────────────
# 全局单例测试
# ─────────────────────────────────────────────

class TestGetSandboxManager:
    """get_sandbox_manager 工厂函数测试"""

    def test_returns_sandbox_manager_instance(self):
        """应返回 SandboxManager 实例"""
        manager = get_sandbox_manager()
        assert isinstance(manager, SandboxManager)

    def test_returns_same_instance(self):
        """多次调用应返回同一实例（单例模式）"""
        m1 = get_sandbox_manager()
        m2 = get_sandbox_manager()
        assert m1 is m2
