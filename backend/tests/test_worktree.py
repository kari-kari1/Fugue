"""Git Worktree Manager 测试"""
import os
import subprocess
import pytest


def _init_git_repo(path: str) -> None:
    """在给定路径初始化一个 git 仓库并创建初始提交"""
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@fugue.dev"],
        cwd=path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path, check=True, capture_output=True,
    )
    # 创建初始文件并提交
    init_file = os.path.join(path, "README.md")
    with open(init_file, "w", encoding="utf-8") as f:
        f.write("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=path, check=True, capture_output=True,
    )


@pytest.mark.asyncio
async def test_create_worktree(tmp_path):
    """创建 worktree，验证路径存在且包含 .git 文件"""
    from app.services.worktree_manager import WorktreeManager

    repo_path = str(tmp_path / "main_repo")
    os.makedirs(repo_path)
    _init_git_repo(repo_path)

    manager = WorktreeManager(base_worktree_dir=str(tmp_path / "worktrees"))
    worktree_path = await manager.create_worktree(
        repo_path=repo_path,
        worktree_name="agent-1",
    )

    try:
        assert os.path.isdir(worktree_path)
        git_file = os.path.join(worktree_path, ".git")
        assert os.path.isfile(git_file)
    finally:
        await manager.remove_worktree(worktree_path, force=True)


@pytest.mark.asyncio
async def test_worktree_isolation(tmp_path):
    """两个 worktree 互不影响，各自有独立的文件"""
    from app.services.worktree_manager import WorktreeManager

    repo_path = str(tmp_path / "main_repo")
    os.makedirs(repo_path)
    _init_git_repo(repo_path)

    manager = WorktreeManager(base_worktree_dir=str(tmp_path / "worktrees"))

    wt1_path = await manager.create_worktree(
        repo_path=repo_path,
        worktree_name="agent-1",
    )
    wt2_path = await manager.create_worktree(
        repo_path=repo_path,
        worktree_name="agent-2",
    )

    try:
        # 在 wt1 中创建文件
        with open(os.path.join(wt1_path, "agent1_only.txt"), "w", encoding="utf-8") as f:
            f.write("agent1 data")

        # 在 wt2 中创建文件
        with open(os.path.join(wt2_path, "agent2_only.txt"), "w", encoding="utf-8") as f:
            f.write("agent2 data")

        # wt1 不应有 wt2 的文件
        assert not os.path.exists(os.path.join(wt1_path, "agent2_only.txt"))
        # wt2 不应有 wt1 的文件
        assert not os.path.exists(os.path.join(wt2_path, "agent1_only.txt"))
    finally:
        await manager.remove_worktree(wt1_path, force=True)
        await manager.remove_worktree(wt2_path, force=True)


@pytest.mark.asyncio
async def test_merge_worktree_changes(tmp_path):
    """将 worktree 分支合并回 main"""
    from app.services.worktree_manager import WorktreeManager

    repo_path = str(tmp_path / "main_repo")
    os.makedirs(repo_path)
    _init_git_repo(repo_path)

    manager = WorktreeManager(base_worktree_dir=str(tmp_path / "worktrees"))
    worktree_path = await manager.create_worktree(
        repo_path=repo_path,
        worktree_name="agent-merge",
        branch_name="feature-branch",
    )

    # 在 worktree 中做修改并提交
    new_file = os.path.join(worktree_path, "new_feature.txt")
    with open(new_file, "w", encoding="utf-8") as f:
        f.write("feature content\n")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add feature"],
        cwd=worktree_path, check=True, capture_output=True,
    )

    # 合并回 main
    result = await manager.merge_worktree(
        repo_path=repo_path,
        branch_name="feature-branch",
        target_branch="main",
    )

    try:
        assert result is True
        # 验证 main 分支上存在该文件
        assert os.path.isfile(os.path.join(repo_path, "new_feature.txt"))
    finally:
        await manager.remove_worktree(worktree_path, force=True)


@pytest.mark.asyncio
async def test_cleanup_worktree_on_failure(tmp_path):
    """强制删除 worktree 不抛异常"""
    from app.services.worktree_manager import WorktreeManager

    repo_path = str(tmp_path / "main_repo")
    os.makedirs(repo_path)
    _init_git_repo(repo_path)

    manager = WorktreeManager(base_worktree_dir=str(tmp_path / "worktrees"))
    worktree_path = await manager.create_worktree(
        repo_path=repo_path,
        worktree_name="agent-cleanup",
    )

    assert os.path.isdir(worktree_path)

    # 强制删除不应抛异常
    result = await manager.remove_worktree(worktree_path, force=True)
    assert result is True


@pytest.mark.asyncio
async def test_create_worktree_rejects_invalid_name(tmp_path):
    """create_worktree 应拒绝非法名称（路径遍历、flag 注入、空字符串）"""
    from app.services.worktree_manager import WorktreeManager

    repo_path = str(tmp_path / "main_repo")
    os.makedirs(repo_path)
    _init_git_repo(repo_path)

    manager = WorktreeManager(base_worktree_dir=str(tmp_path / "worktrees"))

    invalid_names = [
        "../escape",       # path traversal
        "../../etc/attack", # deeper path traversal
        "--flag",           # git flag injection
        "-f",               # short flag injection
        "",                 # empty string
        "name with spaces", # spaces
        "name/slash",       # slash
    ]

    for bad_name in invalid_names:
        with pytest.raises(ValueError, match="Invalid worktree name"):
            await manager.create_worktree(
                repo_path=repo_path,
                worktree_name=bad_name,
            )


@pytest.mark.asyncio
async def test_list_worktrees(tmp_path):
    """列出 worktrees 返回正确数量"""
    from app.services.worktree_manager import WorktreeManager

    repo_path = str(tmp_path / "main_repo")
    os.makedirs(repo_path)
    _init_git_repo(repo_path)

    manager = WorktreeManager(base_worktree_dir=str(tmp_path / "worktrees"))
    wt1 = await manager.create_worktree(
        repo_path=repo_path,
        worktree_name="agent-list-1",
    )
    wt2 = await manager.create_worktree(
        repo_path=repo_path,
        worktree_name="agent-list-2",
    )

    try:
        worktrees = await manager.list_worktrees(repo_path)
        # 主仓库 + 2 个 worktree = 3
        assert len(worktrees) == 3
    finally:
        await manager.remove_worktree(wt1, force=True)
        await manager.remove_worktree(wt2, force=True)
