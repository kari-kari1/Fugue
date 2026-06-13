"""Skills API — 报告第6章：技能管理完整 CRUD + 导入 + 沙箱 + 权限"""

import json
import logging
import os
import tempfile
import zipfile
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.models.skill import Skill
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    version: str = "1.0.0"
    author: Optional[str] = None
    author_url: Optional[str] = None
    license: str = "MIT"
    category: Optional[str] = None
    tags: List[str] = []
    config: dict = {}
    code_path: Optional[str] = None
    entrypoint: dict = {}
    required_tools: List[str] = []
    prompt_template: Optional[str] = None
    task_template: dict = {}
    active: bool = True


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    config: Optional[dict] = None
    entrypoint: Optional[dict] = None
    required_tools: Optional[List[str]] = None
    prompt_template: Optional[str] = None
    task_template: Optional[dict] = None
    active: Optional[bool] = None


class SkillResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    version: str
    author: Optional[str]
    category: Optional[str]
    tags: List[str]
    config: dict
    entrypoint: dict
    required_tools: List[str]
    prompt_template: Optional[str]
    task_template: dict
    active: bool
    star_count: str
    install_count: str
    verified: bool
    created_at: str

    model_config = {"from_attributes": True}


# ─── 权限依赖 ────────────────────────────────────────────────────────────────

def _require_admin(user):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="仅管理员可管理技能")


# ─── CRUD 端点 ───────────────────────────────────────────────────────────────

@router.get("/", response_model=dict)
async def list_skills(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    """列出所有技能（DB + 内置注册表）"""
    # 内置技能（注册表）
    from app.plugins.skills import get_skill_registry
    registry = get_skill_registry()
    registry_skills = []
    if search:
        registry_skills = registry.search(search)
    else:
        tags_filter = [tag] if tag else None
        registry_skills = registry.list_skills(category=category, tags=tags_filter)

    # DB 技能
    query = select(Skill)
    if active_only:
        query = query.where(Skill.active == True)
    if category:
        query = query.where(Skill.category == category)
    if search:
        query = query.where(
            (Skill.name.ilike(f"%{search}%")) | (Skill.description.ilike(f"%{search}%"))
        )
    result = await db.execute(query)
    db_skills = result.scalars().all()

    combined = [s.to_dict() for s in registry_skills]
    for s in db_skills:
        combined.append({
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "version": s.version,
            "author": s.author,
            "category": s.category,
            "tags": s.tags or [],
            "config": s.config or {},
            "entrypoint": s.entrypoint or {},
            "required_tools": s.required_tools or [],
            "prompt_template": s.prompt_template,
            "task_template": s.task_template or {},
            "active": s.active,
            "star_count": int(s.star_count or 0),
            "install_count": int(s.install_count or 0),
            "verified": s.verified,
            "created_at": str(s.created_at),
        })

    categories = registry.get_categories()
    for s in db_skills:
        if s.category and s.category not in dict(categories):
            categories[s.category] = 1

    return {"skills": combined, "total": len(combined), "categories": categories}


@router.get("/categories")
async def list_skill_categories(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """获取技能分类列表"""
    from app.plugins.skills import get_skill_registry
    registry = get_skill_registry()
    categories = registry.get_categories()
    result = await db.execute(select(Skill.category).distinct().where(Skill.category.isnot(None)))
    for row in result.scalars().all():
        if row not in dict(categories):
            categories[row] = 1
    return {"categories": categories}


@router.post("/", response_model=dict)
async def create_skill(
    body: SkillCreate,
    current_user: CurrentUser,  # admin check below
    db: AsyncSession = Depends(get_db),
):
    """创建新技能（管理员）"""
    _require_admin(current_user)
    existing = await db.execute(select(Skill).where(Skill.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"技能 '{body.name}' 已存在")

    skill = Skill(
        name=body.name,
        description=body.description,
        version=body.version,
        author=body.author,
        author_url=body.author_url,
        license=body.license,
        category=body.category,
        tags=body.tags,
        config=body.config,
        code_path=body.code_path,
        entrypoint=body.entrypoint,
        required_tools=body.required_tools,
        prompt_template=body.prompt_template,
        task_template=body.task_template,
        active=body.active,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)

    logger.info(f"Skill created: {skill.name}")
    return {"message": "技能创建成功", "skill": {"id": str(skill.id), "name": skill.name}}


@router.get("/{skill_id}")
async def get_skill(
    skill_id: str, current_user: CurrentUser, db: AsyncSession = Depends(get_db)
):
    """获取技能详情"""
    # 先查注册表
    from app.plugins.skills import get_skill_registry
    registry = get_skill_registry()
    reg_skill = registry.get(skill_id)
    if reg_skill:
        return reg_skill.to_dict()

    # 再查 DB
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")

    return {
        "id": str(skill.id), "name": skill.name, "description": skill.description,
        "version": skill.version, "author": skill.author, "category": skill.category,
        "tags": skill.tags or [], "config": skill.config or {},
        "entrypoint": skill.entrypoint or {}, "required_tools": skill.required_tools or [],
        "prompt_template": skill.prompt_template, "task_template": skill.task_template or {},
        "active": skill.active, "star_count": int(skill.star_count or 0),
        "install_count": int(skill.install_count or 0), "verified": skill.verified,
        "created_at": str(skill.created_at),
    }


@router.put("/{skill_id}")
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    current_user: CurrentUser,  # admin check below
    db: AsyncSession = Depends(get_db),
):
    """更新技能（管理员）"""
    _require_admin(current_user)
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(skill, key):
            setattr(skill, key, value)

    await db.commit()
    logger.info(f"Skill updated: {skill.name}")
    return {"message": "技能更新成功", "skill": {"id": str(skill.id), "name": skill.name}}


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    current_user: CurrentUser,  # admin check below
    db: AsyncSession = Depends(get_db),
):
    """删除技能（管理员）"""
    _require_admin(current_user)
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")

    await db.delete(skill)
    await db.commit()
    logger.info(f"Skill deleted: {skill.name}")
    return {"message": f"技能 '{skill.name}' 已删除"}


@router.post("/{skill_id}/activate")
async def toggle_skill_active(
    skill_id: str,
    current_user: CurrentUser,  # admin check below
    db: AsyncSession = Depends(get_db),
):
    """启用/禁用技能"""
    _require_admin(current_user)
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")

    skill.active = not skill.active
    await db.commit()
    return {"message": f"技能已{'启用' if skill.active else '禁用'}", "active": skill.active}


# ─── 导入端点 ────────────────────────────────────────────────────────────────

@router.post("/import/json")
async def import_skill_json(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """从 JSON/YAML 文件导入技能"""
    _require_admin(current_user)
    if not file.filename or not file.filename.endswith(('.json', '.yaml', '.yml')):
        raise HTTPException(status_code=400, detail="仅支持 .json / .yaml / .yml 文件")

    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # 尝试 YAML
        try:
            import yaml
            data = yaml.safe_load(content)
        except Exception:
            raise HTTPException(status_code=400, detail="无法解析文件，请提供有效的 JSON 或 YAML")

    if not data.get("name"):
        raise HTTPException(status_code=400, detail="技能定义必须包含 'name' 字段")

    existing = await db.execute(select(Skill).where(Skill.name == data.get("name")))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"技能 '{data['name']}' 已存在")

    skill = Skill(
        name=data.get("name"),
        description=data.get("description"),
        version=data.get("version", "1.0.0"),
        author=data.get("author"),
        author_url=data.get("author_url"),
        license=data.get("license", "MIT"),
        category=data.get("category"),
        tags=data.get("tags", []),
        config=data,
        entrypoint=data.get("entrypoint", {}),
        required_tools=data.get("required_tools", []),
        prompt_template=data.get("prompt_template"),
        task_template=data.get("task_template", {}),
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)

    logger.info(f"Skill imported from JSON: {skill.name}")
    return {"message": f"技能 '{skill.name}' 导入成功", "id": str(skill.id)}


@router.post("/import/zip")
async def import_skill_zip(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    """从 ZIP 压缩包导入技能（含 plugin.json + 脚本）"""
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="仅支持 .zip 文件")

    content = await file.read()
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "skill.zip")
        with open(zip_path, "wb") as f:
            f.write(content)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            # 查找 plugin.json 或 skill.yaml
            manifest = None
            for name in zf.namelist():
                basename = os.path.basename(name)
                if basename in ('plugin.json', 'skill.json', 'skill.yaml', 'skill.yml'):
                    manifest = name
                    break

            if not manifest:
                raise HTTPException(status_code=400, detail="ZIP 包中缺少 plugin.json 或 skill.yaml")

            zf.extractall(tmpdir)
            manifest_path = os.path.join(tmpdir, manifest)

            with open(manifest_path, encoding='utf-8') as mf:
                if manifest.endswith(('.yaml', '.yml')):
                    import yaml
                    data = yaml.safe_load(mf)
                else:
                    data = json.load(mf)

        if not data.get("name"):
            raise HTTPException(status_code=400, detail="manifest 必须包含 'name'")

        # 保存代码文件路径
        code_dir = os.path.join("skills", data.get("name", "unknown"))
        os.makedirs(code_dir, exist_ok=True)
        for item in os.listdir(tmpdir):
            src = os.path.join(tmpdir, item)
            dst = os.path.join(code_dir, item)
            if os.path.isfile(src) and item != os.path.basename(manifest):
                import shutil
                shutil.copy2(src, dst)

        existing = await db.execute(select(Skill).where(Skill.name == data.get("name")))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"技能 '{data['name']}' 已存在")

        skill = Skill(
            name=data.get("name"),
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            author=data.get("author"),
            config=data,
            code_path=code_dir,
            entrypoint=data.get("entrypoint", {}),
            required_tools=data.get("required_tools", []),
        )
        db.add(skill)
        await db.commit()
        await db.refresh(skill)

        logger.info(f"Skill imported from ZIP: {skill.name}")
        return {"message": f"技能 '{skill.name}' 从 ZIP 导入成功", "id": str(skill.id)}


@router.post("/import/git")
async def import_skill_git(
    current_user: CurrentUser,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    """从 Git URL 导入技能（要求仓库包含 plugin.json）"""
    repo_url = body.get("url")
    if not repo_url:
        raise HTTPException(status_code=400, detail="请提供 Git 仓库 URL")

    with tempfile.TemporaryDirectory() as tmpdir:
        import subprocess
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, tmpdir],
                check=True, capture_output=True, timeout=60,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=400, detail="Git 克隆超时")
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=400, detail=f"Git 克隆失败: {e.stderr.decode()}")

        # 查找 manifest
        manifest_path = None
        for root, dirs, files in os.walk(tmpdir):
            for f in files:
                if f in ('plugin.json', 'skill.json', 'skill.yaml', 'skill.yml'):
                    manifest_path = os.path.join(root, f)
                    break
            if manifest_path:
                break

        if not manifest_path:
            raise HTTPException(status_code=400, detail="仓库中未找到 plugin.json 或 skill.yaml")

        with open(manifest_path, encoding='utf-8') as mf:
            data = json.load(mf) if manifest_path.endswith('.json') else __import__('yaml').safe_load(mf)

        if not data.get("name"):
            raise HTTPException(status_code=400, detail="manifest 必须包含 'name'")

        existing = await db.execute(select(Skill).where(Skill.name == data.get("name")))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"技能 '{data['name']}' 已存在")

        skill = Skill(
            name=data.get("name"),
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            author=data.get("author"),
            config=data,
            entrypoint=data.get("entrypoint", {}),
            required_tools=data.get("required_tools", []),
        )
        db.add(skill)
        await db.commit()
        await db.refresh(skill)

        logger.info(f"Skill imported from Git: {skill.name}")
        return {"message": f"技能 '{skill.name}' 从 Git 导入成功", "id": str(skill.id)}
