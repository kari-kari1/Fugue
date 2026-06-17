"""Git Worktree Manager - 为 Agent 执行提供隔离工作目录"""

import asyncio
import logging
import os
import re
import shutil

logger = logging.getLogger(__name__)


class WorktreeManager:
    """Git Worktree 管理器

    提供隔离的 Git 工作目录，防止多个 Agent 并行执行时的文件冲突。
    """

    def __init__(self, base_worktree_dir: str | None = None) -> None:
        self.base_worktree_dir = base_worktree_dir or os.path.join(
            os.path.expanduser("~"), ".fugue", "worktrees"
        )

    def _validate_worktree_name(self, name: str) -> None:
        """Validate worktree name to prevent path traversal and flag injection."""
        if not name or not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError(
                f"Invalid worktree name: {name!r}. "
                "Must be alphanumeric with _ and - only."
            )
        # Prevent git flag injection (names starting with -)
        if name.startswith("-"):
            raise ValueError(
                f"Invalid worktree name: {name!r}. "
                "Must not start with a dash."
            )
        # Also verify the resolved path is under base_worktree_dir
        resolved = os.path.realpath(os.path.join(self.base_worktree_dir, name))
        if not resolved.startswith(os.path.realpath(self.base_worktree_dir) + os.sep):
            raise ValueError("Worktree path escapes base directory")

    async def _run_git(
        self, args: list[str], cwd: str
    ) -> tuple[int, str, str]:
        """执行 git 命令并返回 (returncode, stdout, stderr)"""
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        return proc.returncode, stdout, stderr

    async def create_worktree(
        self,
        repo_path: str,
        worktree_name: str,
        branch_name: str | None = None,
    ) -> str:
        """创建一个新的 worktree

        Args:
            repo_path: 主仓库路径
            worktree_name: worktree 名称，用于生成子目录
            branch_name: 分支名称，默认为 f"worktree/{worktree_name}"

        Returns:
            worktree 的绝对路径

        Raises:
            ValueError: worktree_name 不合法时抛出
            RuntimeError: git worktree add 失败时抛出
        """
        self._validate_worktree_name(worktree_name)
        os.makedirs(self.base_worktree_dir, exist_ok=True)
        worktree_path = os.path.join(self.base_worktree_dir, worktree_name)
        branch = branch_name or f"worktree/{worktree_name}"

        args = ["worktree", "add", "-b", branch, worktree_path]
        returncode, stdout, stderr = await self._run_git(args, cwd=repo_path)

        if returncode != 0:
            # 清理可能残留的目录
            if os.path.exists(worktree_path):
                shutil.rmtree(worktree_path, ignore_errors=True)
            raise RuntimeError(
                f"git worktree add failed (rc={returncode}): {stderr}"
            )

        logger.info("Created worktree %s at %s", worktree_name, worktree_path)
        return worktree_path

    async def remove_worktree(
        self, worktree_path: str, force: bool = False
    ) -> bool:
        """移除一个 worktree

        Args:
            worktree_path: worktree 目录路径
            force: 是否强制移除

        Returns:
            成功返回 True
        """
        if not os.path.isdir(worktree_path):
            logger.warning("Worktree path does not exist: %s", worktree_path)
            return True

        # 从 .git 文件中获取主仓库路径
        git_file = os.path.join(worktree_path, ".git")
        repo_path = self._find_main_repo(worktree_path, git_file)

        if repo_path:
            args = ["worktree", "remove"]
            if force:
                args.append("--force")
            args.append(worktree_path)

            returncode, stdout, stderr = await self._run_git(args, cwd=repo_path)

            if returncode == 0:
                logger.info("Removed worktree at %s", worktree_path)
                return True

            logger.warning(
                "git worktree remove failed (rc=%d): %s", returncode, stderr
            )

        # 回退到直接删除目录
        shutil.rmtree(worktree_path, ignore_errors=True)
        logger.info("Force removed worktree directory at %s", worktree_path)
        return True

    async def merge_worktree(
        self,
        repo_path: str,
        branch_name: str,
        target_branch: str = "main",
    ) -> bool:
        """将 worktree 的分支合并回主仓库的目标分支

        Args:
            repo_path: 主仓库路径
            branch_name: 要合并的分支名称
            target_branch: 目标分支，默认 "main"

        Returns:
            合并成功返回 True，失败返回 False
        """
        # checkout 目标分支
        rc, _, stderr = await self._run_git(
            ["checkout", target_branch], cwd=repo_path
        )
        if rc != 0:
            logger.error("Failed to checkout %s: %s", target_branch, stderr)
            return False

        # 合并
        rc, _, stderr = await self._run_git(
            ["merge", "--no-ff", branch_name], cwd=repo_path
        )
        if rc != 0:
            logger.error(
                "Failed to merge %s into %s: %s",
                branch_name, target_branch, stderr,
            )
            # 中止合并以恢复仓库状态
            await self._run_git(["merge", "--abort"], cwd=repo_path)
            return False

        logger.info(
            "Merged branch %s into %s", branch_name, target_branch
        )
        return True

    async def list_worktrees(self, repo_path: str) -> list[dict[str, str]]:
        """列出主仓库下的所有 worktrees

        Args:
            repo_path: 主仓库路径

        Returns:
            worktree 信息列表，每个元素包含 path, head, branch 等字段
        """
        rc, stdout, stderr = await self._run_git(
            ["worktree", "list", "--porcelain"], cwd=repo_path
        )
        if rc != 0:
            logger.error("Failed to list worktrees: %s", stderr)
            return []

        return self._parse_porcelain(stdout)

    @staticmethod
    def _parse_porcelain(output: str) -> list[dict[str, str]]:
        """解析 git worktree list --porcelain 输出"""
        worktrees: list[dict[str, str]] = []
        current: dict[str, str] = {}

        for line in output.strip().splitlines():
            if not line.strip():
                if current:
                    worktrees.append(current)
                    current = {}
                continue

            if " " in line:
                key, _, value = line.partition(" ")
                current[key] = value
            else:
                # bare 标记行（如 "bare"）没有值
                current[line] = ""

        if current:
            worktrees.append(current)

        return worktrees

    @staticmethod
    def _find_main_repo(worktree_path: str, git_file: str) -> str | None:
        """从 .git 文件中解析主仓库路径"""
        if not os.path.isfile(git_file):
            return None

        try:
            with open(git_file, encoding="utf-8") as f:
                content = f.read().strip()
            # .git 文件格式: gitdir: /path/to/main-repo/.git/worktrees/<name>
            if content.startswith("gitdir: "):
                gitdir = content[len("gitdir: "):]
                # 向上两级：worktrees/<name> -> .git -> repo
                main_git_dir = os.path.dirname(os.path.dirname(gitdir))
                return os.path.dirname(main_git_dir)
        except OSError:
            pass

        return None


# 全局单例
_manager: WorktreeManager | None = None


def get_worktree_manager() -> WorktreeManager:
    """获取 WorktreeManager 全局单例"""
    global _manager
    if _manager is None:
        _manager = WorktreeManager()
    return _manager
