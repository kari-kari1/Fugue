"""Skills 功能扩展模块

报告第2章 Marketplace (4/10) + 第5章要求:
- Skills 功能扩展模块: 可复用的任务模板 + 上下文感知的技能匹配
- 第三方开发者接入: 标准化的 Skill 定义接口
- 与 Marketplace 集成: 技能的发布、发现、安装
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillDefinition:
    """技能定义 — 标准化接口"""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    # 技能参数定义
    parameters: Dict[str, Any] = field(default_factory=dict)
    # 所需工具列表
    required_tools: List[str] = field(default_factory=list)
    # Agent 角色提示词模板
    prompt_template: str = ""
    # 任务配置模板
    task_template: Dict[str, Any] = field(default_factory=dict)
    # 执行配置
    config: Dict[str, Any] = field(default_factory=dict)
    # 评分和统计
    star_count: int = 0
    install_count: int = 0
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "parameters": self.parameters,
            "required_tools": self.required_tools,
            "prompt_template": self.prompt_template,
            "task_template": self.task_template,
            "config": self.config,
            "star_count": self.star_count,
            "install_count": self.install_count,
            "verified": self.verified,
        }


class SkillRegistry:
    """技能注册中心 — 管理技能的注册、发现、执行"""

    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = {}
        self._executors: Dict[str, Callable] = {}

    def register(self, skill: SkillDefinition, executor: Optional[Callable] = None):
        """注册技能"""
        self._skills[skill.name] = skill
        if executor:
            self._executors[skill.name] = executor
        logger.info("Skill registered: %s v%s", skill.name, skill.version)

    def unregister(self, name: str):
        """注销技能"""
        self._skills.pop(name, None)
        self._executors.pop(name, None)

    def get(self, name: str) -> Optional[SkillDefinition]:
        return self._skills.get(name)

    def list_skills(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[SkillDefinition]:
        """列出技能，支持按分类和标签过滤"""
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        if tags:
            skills = [s for s in skills if any(t in s.tags for t in tags)]
        return sorted(skills, key=lambda s: (-s.verified, -s.install_count, s.name))

    def search(self, query: str) -> List[SkillDefinition]:
        """搜索技能"""
        query_lower = query.lower()
        results = []
        for skill in self._skills.values():
            if (query_lower in skill.name.lower()
                    or query_lower in skill.description.lower()
                    or any(query_lower in tag.lower() for tag in skill.tags)):
                results.append(skill)
        return results

    def get_categories(self) -> List[Dict[str, Any]]:
        """获取技能分类列表及计数"""
        counts: Dict[str, int] = {}
        for skill in self._skills.values():
            counts[skill.category] = counts.get(skill.category, 0) + 1
        return [{"id": k, "name": k, "count": v} for k, v in sorted(counts.items())]

    async def execute(self, name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行技能"""
        skill = self._skills.get(name)
        if not skill:
            return {"success": False, "error": f"技能 '{name}' 不存在"}

        executor = self._executors.get(name)
        if not executor:
            return {"success": False, "error": f"技能 '{name}' 未注册执行器"}

        try:
            result = await executor(params or {})
            return {"success": True, "result": result}
        except Exception as e:
            logger.error("Skill execution failed: %s - %s", name, e)
            return {"success": False, "error": str(e)}

    def load_from_directory(self, directory: str):
        """从目录加载技能定义文件 (JSON/YAML)"""
        skill_dir = Path(directory)
        if not skill_dir.exists():
            return

        for f in skill_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                skill = SkillDefinition(**data)
                self.register(skill)
            except Exception as e:
                logger.warning("Failed to load skill from %s: %s", f, e)


# ─── 内置技能 ──────────────────────────────────────────────────────────────

BUILTIN_SKILLS = [
    SkillDefinition(
        name="deep-research",
        description="深度调研：多源搜索 → 信息提取 → 交叉验证 → 综合报告",
        category="research",
        tags=["research", "search", "analysis"],
        version="1.0.0",
        author="AgentForge",
        verified=True,
        required_tools=["web_search", "text_analysis"],
        prompt_template="你是一个专业调研员。请对以下主题进行深度调研：\n\n{topic}\n\n要求：\n1. 从多个来源搜索信息\n2. 提取关键事实和数据\n3. 交叉验证不同来源的信息\n4. 生成结构化的调研报告",
        task_template={
            "tasks": [
                {"name": "信息搜索", "description": "从多个渠道搜索相关信息", "expected_output": "原始搜索结果列表"},
                {"name": "信息提取", "description": "从搜索结果中提取关键信息", "expected_output": "结构化关键信息"},
                {"name": "交叉验证", "description": "验证不同来源信息的一致性", "description": "验证结果和可信度评估"},
                {"name": "综合报告", "description": "整合所有信息生成最终报告", "expected_output": "完整的调研报告"},
            ]
        },
        parameters={
            "topic": {"type": "string", "description": "调研主题", "required": True},
            "depth": {"type": "string", "enum": ["quick", "standard", "deep"], "default": "standard"},
            "language": {"type": "string", "default": "zh-CN"},
        },
    ),
    SkillDefinition(
        name="code-review",
        description="代码审查：安全性 → 性能 → 可维护性 → 最佳实践",
        category="development",
        tags=["code", "review", "security", "quality"],
        version="1.0.0",
        author="AgentForge",
        verified=True,
        required_tools=["file_read", "text_analysis"],
        prompt_template="你是一个资深代码审查员。请审查以下代码：\n\n{code}\n\n从安全性、性能、可维护性、最佳实践四个维度进行审查。",
        parameters={
            "code": {"type": "string", "description": "待审查的代码", "required": True},
            "language": {"type": "string", "description": "编程语言"},
            "focus": {"type": "string", "enum": ["security", "performance", "all"], "default": "all"},
        },
    ),
    SkillDefinition(
        name="content-writer",
        description="内容创作：大纲规划 → 初稿撰写 → 润色优化 → SEO适配",
        category="writing",
        tags=["writing", "content", "blog", "seo"],
        version="1.0.0",
        author="AgentForge",
        verified=True,
        required_tools=["web_search", "file_write"],
        prompt_template="你是一个专业内容创作者。请围绕以下主题创作内容：\n\n{topic}\n\n要求：\n1. 规划清晰的大纲结构\n2. 撰写高质量的初稿\n3. 润色语言表达\n4. 适配SEO关键词",
        parameters={
            "topic": {"type": "string", "description": "内容主题", "required": True},
            "type": {"type": "string", "enum": ["blog", "article", "report", "tutorial"], "default": "article"},
            "word_count": {"type": "integer", "default": 2000},
        },
    ),
    SkillDefinition(
        name="data-analyst",
        description="数据分析：数据清洗 → 统计分析 → 洞察提取 → 可视化建议",
        category="data",
        tags=["data", "analysis", "statistics", "visualization"],
        version="1.0.0",
        author="AgentForge",
        verified=True,
        required_tools=["database_query", "text_analysis"],
        prompt_template="你是一个数据分析师。请分析以下数据：\n\n{data_description}\n\n要求：\n1. 数据清洗和预处理\n2. 统计分析\n3. 提取关键洞察\n4. 给出可视化建议",
        parameters={
            "data_description": {"type": "string", "description": "数据描述或查询", "required": True},
            "analysis_type": {"type": "string", "enum": ["descriptive", "diagnostic", "predictive"], "default": "descriptive"},
        },
    ),
]


# ─── 全局单例 ──────────────────────────────────────────────────────────────

_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
        # 注册内置技能
        for skill in BUILTIN_SKILLS:
            _skill_registry.register(skill)
    return _skill_registry
