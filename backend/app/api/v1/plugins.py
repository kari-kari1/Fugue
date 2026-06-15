"""插件管理API"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user import User
from app.plugins.manager import get_plugin_manager
from app.plugins.loader import get_plugin_loader
from app.plugins.sandbox import get_sandbox_pool

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── 请求/响应模型 ───


class PluginInstallRequest(BaseModel):
    """安装插件请求"""
    plugin_name: str = Field(..., min_length=1, max_length=100)
    source: str = Field(default="local", description="来源：local/marketplace/github")
    config: Optional[Dict[str, Any]] = None


class PluginExecuteRequest(BaseModel):
    """执行工具请求"""
    tool_name: str = Field(..., min_length=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)


class PluginReloadRequest(BaseModel):
    """重新加载插件请求"""
    plugin_name: str = Field(..., min_length=1)


# ─── API端点 ───


@router.get("/")
async def list_plugins(
    current_user: User = Depends(get_current_user),
):
    """列出所有已加载的插件"""
    manager = get_plugin_manager()
    plugins = manager.list_plugins()

    return {
        "plugins": plugins,
        "total": len(plugins),
    }


@router.get("/tools")
async def list_tools(
    category: Optional[str] = Query(None, description="按分类过滤"),
    permission: Optional[str] = Query(None, description="按权限等级过滤"),
    current_user: User = Depends(get_current_user),
):
    """列出所有可用工具"""
    manager = get_plugin_manager()

    if category:
        tools = manager.get_tools_by_category(category)
    elif permission:
        tools = manager.get_tools_by_permission(permission)
    else:
        tools = list(manager.tools.values())

    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "permissions": tool.permissions,
                "category": tool.category,
                "version": tool.version,
            }
            for tool in tools
        ],
        "total": len(tools),
    }


@router.get("/{plugin_name}")
async def get_plugin_detail(
    plugin_name: str,
    current_user: User = Depends(get_current_user),
):
    """获取插件详情"""
    manager = get_plugin_manager()
    plugin = manager.get_plugin(plugin_name)

    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")

    return plugin.to_dict()


@router.post("/execute/{tool_name}")
async def execute_tool(
    tool_name: str,
    request: PluginExecuteRequest,
    current_user: User = Depends(get_current_user),
):
    """执行工具"""
    manager = get_plugin_manager()
    tool = manager.get_tool(tool_name)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    # 检查权限
    if tool.permissions == "dangerous":
        # 危险操作需要额外确认
        logger.warning(f"Dangerous tool execution requested: {tool_name} by user {current_user.id}")

    try:
        # 使用沙箱执行
        sandbox_pool = get_sandbox_pool()
        result = await sandbox_pool.execute(
            plugin_name=tool.func.__self__.name,
            tool_name=tool_name,
            func=tool.func,
            arguments=request.arguments,
            timeout=30,
        )

        return {
            "success": True,
            "tool_name": tool_name,
            "result": result,
        }

    except TimeoutError:
        raise HTTPException(status_code=408, detail=f"Tool '{tool_name}' execution timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


@router.get("/schemas/openai")
async def get_openai_schemas(
    category: Optional[str] = Query(None),
    permission: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """获取OpenAI格式的工具Schema"""
    manager = get_plugin_manager()
    categories = [category] if category else None
    permissions = [permission] if permission else None

    schemas = manager.get_openai_tools_schema(
        categories=categories,
        permissions=permissions,
    )

    return {
        "schemas": schemas,
        "count": len(schemas),
    }


@router.get("/schemas/anthropic")
async def get_anthropic_schemas(
    category: Optional[str] = Query(None),
    permission: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """获取Anthropic格式的工具Schema"""
    manager = get_plugin_manager()
    categories = [category] if category else None
    permissions = [permission] if permission else None

    schemas = manager.get_anthropic_tools_schema(
        categories=categories,
        permissions=permissions,
    )

    return {
        "schemas": schemas,
        "count": len(schemas),
    }


@router.post("/reload")
async def reload_plugin(
    request: PluginReloadRequest,
    current_user: User = Depends(get_current_user),
):
    """重新加载插件（开发模式）"""
    loader = get_plugin_loader()

    try:
        loader.reload_plugin(request.plugin_name)
        return {
            "success": True,
            "message": f"Plugin '{request.plugin_name}' reloaded successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Plugin reload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Plugin reload failed: {str(e)}")


@router.post("/health-check")
async def health_check_plugins(
    current_user: User = Depends(get_current_user),
):
    """对所有插件执行健康检查"""
    manager = get_plugin_manager()
    results = await manager.health_check_all()

    return {
        "results": results,
        "total": len(results),
        "healthy_count": sum(1 for r in results.values() if r.get("healthy")),
    }


@router.get("/active-executions")
async def get_active_executions(
    current_user: User = Depends(get_current_user),
):
    """获取活跃的工具执行"""
    sandbox_pool = get_sandbox_pool()

    return {
        "active_count": sandbox_pool.get_active_count(),
        "executions": sandbox_pool.get_active_executions(),
    }
