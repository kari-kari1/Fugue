"""Agent 执行沙箱 — 使用 bubblewrap / Docker 进行文件系统与网络隔离"""

import asyncio
import logging
import os
import re
import shlex
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SandboxType(str, Enum):
    """沙箱类型枚举"""
    NONE = "none"          # 开发模式（无隔离）
    BWRAP = "bwrap"        # bubblewrap（Linux）
    DOCKER = "docker"      # Docker 容器
    SEATBELT = "seatbelt"  # macOS sandbox-exec


@dataclass
class SandboxConfig:
    """沙箱配置"""
    enable_filesystem_isolation: bool = True
    enable_network_isolation: bool = False
    allowed_paths: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(default_factory=lambda: [
        "rm -rf /",
        "rm -rf /*",
        "dd if=",
        "mkfs",
        ":(){ :|:& };:",
        "chmod 777 /",
        "chown root",
    ])
    max_execution_time: int = 300       # 秒
    max_memory_mb: int = 512            # MB
    max_cpu_percent: int = 50           # %


class SandboxManager:
    """沙箱执行管理器

    检测当前平台可用的沙箱后端，对工具命令进行安全验证，
    并在选定的沙箱中执行命令。
    """

    def __init__(self):
        self.available_sandboxes: List[SandboxType] = []
        self._detect_available_sandboxes()

    # ── 沙箱检测 ─────────────────────────────────────────

    def _detect_available_sandboxes(self):
        """检测当前平台可用的沙箱类型，结果写入 self.available_sandboxes"""
        # NONE 模式始终可用（开发/调试用）
        self.available_sandboxes = [SandboxType.NONE]

        if sys.platform == "linux":
            if shutil.which("bwrap"):
                self.available_sandboxes.append(SandboxType.BWRAP)
                logger.info("bubblewrap (bwrap) 可用")
            else:
                logger.info("bubblewrap (bwrap) 不可用，未安装")

        if shutil.which("docker"):
            if self._check_docker_daemon():
                self.available_sandboxes.append(SandboxType.DOCKER)
                logger.info("Docker 可用（守护进程运行中）")
            else:
                logger.info("Docker 命令存在但守护进程未运行，跳过")

        if sys.platform == "darwin":
            if shutil.which("sandbox-exec"):
                self.available_sandboxes.append(SandboxType.SEATBELT)
                logger.info("macOS sandbox-exec 可用")

    @staticmethod
    def _check_docker_daemon() -> bool:
        """快速检测 Docker 守护进程是否可连接（同步，超时 2 秒）"""
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    # ── 命令验证 ─────────────────────────────────────────

    def validate_command(self, command: str, config: SandboxConfig) -> Optional[str]:
        """验证命令是否安全。

        Args:
            command: 待执行的 shell 命令
            config:  沙箱配置（含 blocked_commands 列表）

        Returns:
            None 表示安全，否则返回错误信息字符串。
        """
        # 标准化空白符，防止 "rm  -rf  /" 等绕过
        normalized = re.sub(r'\s+', ' ', command.strip())

        # 对 blocked_commands 做子串匹配（标准化后）
        for blocked in config.blocked_commands:
            if blocked.lower() in normalized.lower():
                return f"危险命令被禁止执行: 匹配到规则 '{blocked}'"

        # 额外：提取并检查基础命令名
        try:
            tokens = shlex.split(normalized)
            if tokens:
                base_cmd = os.path.basename(tokens[0])
                # NONE 沙箱模式下阻止已知的高危基础命令
                DANGEROUS_COMMANDS = {'dd', 'mkfs', 'fdisk', 'shutdown', 'reboot', 'halt'}
                if base_cmd in DANGEROUS_COMMANDS:
                    return f"危险命令被禁止执行: 高危命令 '{base_cmd}'"
        except ValueError:
            # shlex.split 对格式错误的命令会抛异常 — 直接拦截
            return "危险命令被禁止执行: 命令格式错误"

        return None

    # ── bwrap 命令构建 ────────────────────────────────────

    def build_bwrap_command(
        self,
        command: str,
        workspace: str,
        config: SandboxConfig,
    ) -> List[str]:
        """构建 bubblewrap 执行命令。

        Args:
            command:   用户命令
            workspace: 工作目录（将作为沙箱根目录的 bind 来源）
            config:    沙箱配置

        Returns:
            完整的 bwrap 命令列表（可直接传给 asyncio.create_subprocess_exec）
        """
        cmd: List[str] = [
            "bwrap",
            "--unshare-all",           # 隔离所有命名空间
            "--die-with-parent",       # 父进程退出时终止
            "--ro-bind", "/", "/",     # 只读挂载宿主根目录
            "--tmpfs", "/tmp",         # 独立的 /tmp
        ]

        # 绑定工作目录（可写）
        cmd += ["--bind", workspace, workspace]

        # 额外的可写路径
        for path in config.allowed_paths:
            cmd += ["--bind", path, path]

        # 资源限制
        cmd += [
            "--unshare-pid",           # PID 隔离
            "--new-session",           # 新 session
        ]

        # 网络隔离（默认已由 --unshare-all 包含，显式声明以增加可读性）
        if config.enable_network_isolation:
            # --unshare-net 已包含在 --unshare-all 中
            pass

        cmd += ["--", "/bin/sh", "-c", command]
        return cmd

    # ── Docker 命令构建 ───────────────────────────────────

    def build_docker_command(
        self,
        command: str,
        workspace: str,
        config: SandboxConfig,
    ) -> List[str]:
        """构建 Docker 执行命令。

        Args:
            command:   用户命令
            workspace: 工作目录（容器内挂载为 /workspace）
            config:    沙箱配置

        Returns:
            完整的 docker run 命令列表
        """
        cmd: List[str] = [
            "docker", "run", "--rm",
            "--network", "none" if config.enable_network_isolation else "bridge",
            "--memory", f"{config.max_memory_mb}m",
            "--cpus", f"{config.max_cpu_percent / 100:.2f}",
            "--workdir", "/workspace",
            "-v", f"{workspace}:/workspace:rw",
        ]

        # 额外挂载的只读/可写路径
        for path in config.allowed_paths:
            cmd += ["-v", f"{path}:{path}:ro"]

        # 超时通过 timeout 命令在容器内实现
        cmd += [
            "python:3.12-slim",
            "/bin/sh", "-c",
            f"timeout {config.max_execution_time} {command}" if sys.platform != "win32"
            else command,
        ]
        return cmd

    # ── 沙箱执行 ─────────────────────────────────────────

    async def execute_in_sandbox(
        self,
        command: str,
        workspace: str,
        config: Optional[SandboxConfig] = None,
        sandbox_type: Optional[SandboxType] = None,
    ) -> Dict:
        """在沙箱中执行命令。

        Args:
            command:      shell 命令
            workspace:    工作目录
            config:       沙箱配置（None 则使用默认值）
            sandbox_type: 指定沙箱类型（None 则自动选择）

        Returns:
            {
                "success": bool,
                "output": str,
                "error": str,
                "exit_code": int,
                "sandbox_type": str,
            }
        """
        config = config or SandboxConfig()

        # 自动选择沙箱类型
        if sandbox_type is None:
            sandbox_type = self._auto_select_sandbox()

        # 命令验证
        validation_error = self.validate_command(command, config)
        if validation_error:
            logger.warning(f"[SANDBOX] 命令被拦截: {command} — {validation_error}")
            return {
                "success": False,
                "output": "",
                "error": validation_error,
                "exit_code": -1,
                "sandbox_type": sandbox_type.value,
            }

        # 构建实际执行命令
        if sandbox_type == SandboxType.BWRAP:
            exec_args = self.build_bwrap_command(command, workspace, config)
        elif sandbox_type == SandboxType.DOCKER:
            exec_args = self.build_docker_command(command, workspace, config)
        else:
            # NONE / SEATBELT: 直接执行
            exec_args = ["/bin/sh", "-c", command] if sys.platform != "win32" \
                else ["cmd", "/c", command]

        # 异步执行并处理超时
        try:
            process = await asyncio.create_subprocess_exec(
                *exec_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=config.max_execution_time,
            )

            stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
            exit_code = process.returncode or 0

            return {
                "success": exit_code == 0,
                "output": stdout,
                "error": stderr,
                "exit_code": exit_code,
                "sandbox_type": sandbox_type.value,
            }

        except asyncio.TimeoutError:
            logger.warning(
                f"[SANDBOX] 命令超时 ({config.max_execution_time}s): {command[:100]}"
            )
            # 尝试终止进程
            try:
                process.kill()
            except (ProcessLookupError, OSError):
                pass

            # 等待进程退出，清理僵尸进程
            try:
                await process.wait()
            except (ProcessLookupError, OSError):
                pass

            return {
                "success": False,
                "output": "",
                "error": f"执行超时（{config.max_execution_time}秒上限）",
                "exit_code": -1,
                "sandbox_type": sandbox_type.value,
            }

        except FileNotFoundError as e:
            logger.error(f"[SANDBOX] 沙箱命令未找到: {e}")
            return {
                "success": False,
                "output": "",
                "error": f"沙箱工具不可用: {str(e)}",
                "exit_code": -1,
                "sandbox_type": sandbox_type.value,
            }

    # ── 内部工具 ─────────────────────────────────────────

    def _auto_select_sandbox(self) -> SandboxType:
        """自动选择最安全的可用沙箱类型。

        优先级: BWRAP > SEATBELT > DOCKER > NONE
        """
        for preferred in (SandboxType.BWRAP, SandboxType.SEATBELT, SandboxType.DOCKER):
            if preferred in self.available_sandboxes:
                return preferred
        return SandboxType.NONE


# ── 全局单例 ──────────────────────────────────────────────

_manager_instance: Optional[SandboxManager] = None


def get_sandbox_manager() -> SandboxManager:
    """获取全局 SandboxManager 单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SandboxManager()
    return _manager_instance
