"""API v1路由"""

from fastapi import APIRouter

from app.api.v1 import auth, crews, agents, tasks, executions, demo, validation, templates, websocket, tools, exports, reviews, knowledge_bases, mcp, plugins, api_keys, published, webhooks, schedules, plugins_marketplace, files, iterations, mcp_server, approvals, skills

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(crews.router, prefix="/crews", tags=["工作流"])
api_router.include_router(agents.router, prefix="/agents", tags=["智能体"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务"])
api_router.include_router(executions.router, prefix="/executions", tags=["执行"])
api_router.include_router(demo.router, prefix="/demo", tags=["演示"])
api_router.include_router(validation.router, prefix="/validation", tags=["校验"])
api_router.include_router(templates.router, prefix="/templates", tags=["模板"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
api_router.include_router(tools.router, prefix="/tools", tags=["工具"])
api_router.include_router(exports.router, prefix="/exports", tags=["导出"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["审核"])
api_router.include_router(knowledge_bases.router, prefix="/knowledge-bases", tags=["知识库"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["MCP"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["插件"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API密钥"])
api_router.include_router(published.router, prefix="/published", tags=["发布工作流"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhook"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["定时任务"])
api_router.include_router(plugins_marketplace.router, prefix="/plugins/marketplace", tags=["Plugin Marketplace"])
api_router.include_router(files.router, prefix="/files", tags=["文件存储"])
api_router.include_router(iterations.router, prefix="/executions", tags=["迭代"])
api_router.include_router(mcp_server.router, prefix="/mcp-server", tags=["MCP Server"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["审批"])
api_router.include_router(skills.router, prefix="/skills", tags=["技能市场"])
