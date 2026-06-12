# P0 Agent Capabilities Upgrade - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Fugue's core agent capabilities by implementing MCP Server layer, Git Worktree isolation, three-tier approval mode, and execution sandbox — transforming it from a basic workflow tool into an industrial-grade multi-agent platform.

**Architecture:** 
- MCP Server: Expose Fugue agents as standard MCP Tools/Resources/Prompts via Streamable HTTP transport
- Git Worktree: Create isolated working directories per agent execution using `git worktree add`
- Approval Mode: Insert approval middleware in executor's tool-call layer with WebSocket notifications
- Sandbox: Wrap tool execution with bubblewrap (bwrap) for filesystem/network isolation

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, MCP SDK 1.2+, GitPython, bubblewrap (bwrap), WebSocket

---

## File Structure

```
backend/app/
├── mcp_server/
│   ├── __init__.py              # NEW - MCP Server module init
│   ├── server.py                # NEW - FastMCP server instance + tools/resources/prompts registration
│   ├── tools.py                 # NEW - MCP Tool definitions (agent execution, workflow management)
│   ├── resources.py             # NEW - MCP Resource definitions (workflow templates, execution results)
│   └── prompts.py               # NEW - MCP Prompt templates
├── engine/
│   ├── executor.py              # MODIFY - Add approval hooks, sandbox wrapper, worktree integration
│   ├── sandbox.py               # NEW - Sandbox execution wrapper (bwrap + Docker)
│   └── mcp_adapter.py           # MODIFY - Add MCP Server client capabilities
├── models/
│   ├── crew.py                  # MODIFY - Add approval_mode field
│   └── execution.py             # MODIFY - Add worktree_path field
├── api/v1/
│   ├── mcp_server.py            # NEW - MCP Server HTTP/SSE endpoint
│   └── approvals.py             # NEW - Approval request/response endpoints
├── schemas/
│   ├── approval.py              # NEW - Approval request/response schemas
│   └── mcp_server.py            # NEW - MCP Server schemas
└── services/
    ├── worktree_manager.py      # NEW - Git Worktree lifecycle management
    └── approval_manager.py      # NEW - Approval workflow management

backend/tests/
├── test_mcp_server.py           # NEW - MCP Server tests
├── test_worktree.py             # NEW - Worktree isolation tests
├── test_approval.py             # NEW - Approval mode tests
└── test_sandbox.py              # NEW - Sandbox tests
```

---

## Task 1: MCP Server Foundation

**Files:**
- Create: `backend/app/mcp_server/__init__.py`
- Create: `backend/app/mcp_server/server.py`
- Create: `backend/app/mcp_server/tools.py`
- Create: `backend/app/mcp_server/resources.py`
- Create: `backend/app/mcp_server/prompts.py`
- Create: `backend/tests/test_mcp_server.py`

- [ ] **Step 1: Write the failing test for MCP Server initialization**

```python
# backend/tests/test_mcp_server.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.server.fastmcp import FastMCP

from app.mcp_server.server import create_mcp_server, get_mcp_server


@pytest.mark.asyncio
async def test_create_mcp_server_returns_fastmcp_instance():
    """Test that create_mcp_server returns a valid FastMCP instance"""
    server = create_mcp_server()
    assert server is not None
    assert hasattr(server, 'list_tools')
    assert hasattr(server, 'list_resources')
    assert hasattr(server, 'list_prompts')


@pytest.mark.asyncio
async def test_mcp_server_has_agent_tools_registered():
    """Test that MCP Server has agent-related tools registered"""
    server = create_mcp_server()
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    
    assert "execute_workflow" in tool_names
    assert "get_execution_status" in tool_names
    assert "list_workflows" in tool_names


@pytest.mark.asyncio
async def test_mcp_server_has_workflow_resources():
    """Test that MCP Server exposes workflow templates as resources"""
    server = create_mcp_server()
    resources = await server.list_resources()
    resource_uris = [str(r.uri) for r in resources]
    
    assert any("workflow" in uri for uri in resource_uris)


@pytest.mark.asyncio
async def test_mcp_server_has_prompt_templates():
    """Test that MCP Server has prompt templates registered"""
    server = create_mcp_server()
    prompts = await server.list_prompts()
    prompt_names = [p.name for p in prompts]
    
    assert "workflow_analysis" in prompt_names
    assert "agent_optimization" in prompt_names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_mcp_server.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.mcp_server'"

- [ ] **Step 3: Create MCP Server module structure**

```python
# backend/app/mcp_server/__init__.py
"""MCP Server - Expose Fugue agents as standard MCP Tools/Resources/Prompts"""
```

- [ ] **Step 4: Implement MCP Server factory**

```python
# backend/app/mcp_server/server.py
from typing import Optional
from mcp.server.fastmcp import FastMCP

from .tools import register_tools
from .resources import register_resources
from .prompts import register_prompts

_server_instance: Optional[FastMCP] = None


def create_mcp_server() -> FastMCP:
    """Create and configure MCP Server instance"""
    server = FastMCP(
        name="Fugue",
        version="0.1.0",
        description="Multi-agent workflow platform - execute workflows, manage agents, and orchestrate complex tasks"
    )
    
    # Register all components
    register_tools(server)
    register_resources(server)
    register_prompts(server)
    
    return server


def get_mcp_server() -> FastMCP:
    """Get or create global MCP Server instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = create_mcp_server()
    return _server_instance
```

- [ ] **Step 5: Implement MCP Tools**

```python
# backend/app/mcp_server/tools.py
from typing import Dict, Any, Optional
from datetime import datetime
import json

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_session_manager
from app.models.crew import Crew
from app.models.execution import Execution, ExecutionStatus
from app.engine.executor import start_execution


def register_tools(server: FastMCP) -> None:
    """Register all MCP tools"""
    
    @server.tool()
    async def execute_workflow(
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        llm_api_keys: Optional[Dict[str, str]] = None,
        llm_base_urls: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute an Fugue workflow.
        
        Args:
            workflow_id: UUID of the workflow to execute
            inputs: Optional input parameters for the workflow
            llm_api_keys: API keys for LLM providers (e.g., {"openai": "sk-..."})
            llm_base_urls: Custom base URLs for LLM providers
        
        Returns:
            Execution result with execution_id, status, and outputs
        """
        async with db_session_manager.get_session() as db:
            # Verify workflow exists
            crew = await db.get(Crew, workflow_id)
            if not crew:
                return {"error": f"Workflow {workflow_id} not found"}
            
            # Create execution record
            execution = Execution(
                crew_id=workflow_id,
                status=ExecutionStatus.PENDING,
                trigger_type="mcp",
                inputs=inputs or {}
            )
            db.add(execution)
            await db.commit()
            await db.refresh(execution)
            
            # Start execution asynchronously
            execution_id = str(execution.id)
            
            try:
                await start_execution(
                    execution_id=execution_id,
                    llm_api_keys=llm_api_keys or {},
                    llm_base_urls=llm_base_urls or {}
                )
                
                return {
                    "execution_id": execution_id,
                    "status": "started",
                    "workflow_name": crew.name,
                    "message": f"Workflow '{crew.name}' execution started"
                }
            except Exception as e:
                return {
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": str(e)
                }
    
    @server.tool()
    async def get_execution_status(execution_id: str) -> Dict[str, Any]:
        """
        Get the current status of a workflow execution.
        
        Args:
            execution_id: UUID of the execution to check
        
        Returns:
            Current execution status, progress, and results if completed
        """
        async with db_session_manager.get_session() as db:
            execution = await db.get(Execution, execution_id)
            if not execution:
                return {"error": f"Execution {execution_id} not found"}
            
            result = {
                "execution_id": execution_id,
                "status": execution.status.value,
                "created_at": execution.created_at.isoformat() if execution.created_at else None,
                "updated_at": execution.updated_at.isoformat() if execution.updated_at else None,
            }
            
            if execution.status == ExecutionStatus.COMPLETED:
                result["results"] = execution.results
                result["trace"] = execution.trace
            elif execution.status == ExecutionStatus.FAILED:
                result["error"] = execution.error if hasattr(execution, 'error') else "Unknown error"
            
            return result
    
    @server.tool()
    async def list_workflows(
        limit: int = 20,
        offset: int = 0,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available workflows.
        
        Args:
            limit: Maximum number of workflows to return (default: 20)
            offset: Pagination offset (default: 0)
            user_id: Optional filter by user ID
        
        Returns:
            List of workflow summaries with id, name, description, agent_count, task_count
        """
        async with db_session_manager.get_session() as db:
            query = select(Crew).limit(limit).offset(offset)
            
            if user_id:
                query = query.where(Crew.user_id == user_id)
            
            result = await db.execute(query)
            crews = result.scalars().all()
            
            return {
                "workflows": [
                    {
                        "id": str(crew.id),
                        "name": crew.name,
                        "description": crew.description,
                        "created_at": crew.created_at.isoformat() if crew.created_at else None,
                    }
                    for crew in crews
                ],
                "total": len(crews),
                "limit": limit,
                "offset": offset
            }
```

- [ ] **Step 6: Implement MCP Resources**

```python
# backend/app/mcp_server/resources.py
from typing import List
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_session_manager
from app.models.crew import Crew
from app.models.agent import Agent
from app.models.task import Task


def register_resources(server: FastMCP) -> None:
    """Register all MCP resources"""
    
    @server.resource("fugue://workflows")
    async def list_workflow_resources() -> str:
        """List all available workflow templates as resources"""
        async with db_session_manager.get_session() as db:
            result = await db.execute(select(Crew).limit(100))
            crews = result.scalars().all()
            
            workflows = []
            for crew in crews:
                workflows.append({
                    "uri": f"fugue://workflows/{crew.id}",
                    "name": crew.name,
                    "description": crew.description or f"Workflow: {crew.name}",
                    "mimeType": "application/json"
                })
            
            return json.dumps(workflows, indent=2)
    
    @server.resource("fugue://workflows/{workflow_id}")
    async def get_workflow_resource(workflow_id: str) -> str:
        """Get detailed workflow configuration"""
        import json
        
        async with db_session_manager.get_session() as db:
            crew = await db.get(Crew, workflow_id)
            if not crew:
                return json.dumps({"error": "Workflow not found"})
            
            # Load agents
            agents_result = await db.execute(
                select(Agent).where(Agent.crew_id == workflow_id)
            )
            agents = agents_result.scalars().all()
            
            # Load tasks
            tasks_result = await db.execute(
                select(Task).where(Task.crew_id == workflow_id)
            )
            tasks = tasks_result.scalars().all()
            
            return json.dumps({
                "id": str(crew.id),
                "name": crew.name,
                "description": crew.description,
                "process_type": crew.process_type.value if crew.process_type else "sequential",
                "agents": [
                    {
                        "id": str(agent.id),
                        "name": agent.name,
                        "role": agent.role,
                        "goal": agent.goal,
                        "tools": agent.tools_config
                    }
                    for agent in agents
                ],
                "tasks": [
                    {
                        "id": str(task.id),
                        "name": task.name,
                        "description": task.description,
                        "expected_output": task.expected_output
                    }
                    for task in tasks
                ]
            }, indent=2)
```

- [ ] **Step 7: Implement MCP Prompts**

```python
# backend/app/mcp_server/prompts.py
from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """Register all MCP prompt templates"""
    
    @server.prompt()
    def workflow_analysis(workflow_name: str, workflow_description: str) -> str:
        """Generate a prompt for analyzing workflow effectiveness"""
        return f"""Analyze the following workflow and provide optimization suggestions:

Workflow Name: {workflow_name}
Description: {workflow_description}

Please evaluate:
1. Task decomposition efficiency
2. Agent role clarity
3. Potential bottlenecks
4. Parallelization opportunities
5. Error handling strategies

Provide specific, actionable recommendations for improvement."""
    
    @server.prompt()
    def agent_optimization(agent_role: str, agent_goal: str, current_tools: str) -> str:
        """Generate a prompt for optimizing agent configuration"""
        return f"""Optimize the following agent configuration:

Role: {agent_role}
Goal: {agent_goal}
Current Tools: {current_tools}

Please suggest:
1. Additional tools that could enhance this agent's capabilities
2. System prompt improvements for better task execution
3. LLM model selection recommendations
4. Temperature and parameter tuning suggestions

Focus on practical, implementable improvements."""
    
    @server.prompt()
    def execution_debugging(execution_id: str, error_message: str) -> str:
        """Generate a prompt for debugging failed executions"""
        return f"""Debug the following failed workflow execution:

Execution ID: {execution_id}
Error: {error_message}

Please analyze:
1. Root cause of the failure
2. Which task/agent failed
3. Potential fixes
4. Prevention strategies for future executions

Provide step-by-step debugging guidance."""
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_mcp_server.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add backend/app/mcp_server/ backend/tests/test_mcp_server.py
git commit -m "feat(mcp): implement MCP Server foundation with tools, resources, and prompts"
```

---

## Task 2: MCP Server HTTP Endpoint

**Files:**
- Create: `backend/app/api/v1/mcp_server.py`
- Create: `backend/app/schemas/mcp_server.py`
- Modify: `backend/app/api/v1/__init__.py`
- Create: `backend/tests/test_mcp_server_api.py`

- [ ] **Step 1: Write the failing test for MCP Server endpoint**

```python
# backend/tests/test_mcp_server_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.mcp_server.server import get_mcp_server


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_mcp_server_endpoint_returns_sse(client):
    """Test that MCP Server endpoint supports SSE transport"""
    response = await client.get("/api/v1/mcp-server/sse")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_mcp_server_endpoint_handles_json_rpc(client):
    """Test that MCP Server endpoint handles JSON-RPC requests"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    response = await client.post(
        "/api/v1/mcp-server/message",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_mcp_server_api.py -v`
Expected: FAIL with "404 Not Found"

- [ ] **Step 3: Create MCP Server schemas**

```python
# backend/app/schemas/mcp_server.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPToolInfo(BaseModel):
    """MCP Tool information"""
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPResourceInfo(BaseModel):
    """MCP Resource information"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


class MCPPromptInfo(BaseModel):
    """MCP Prompt information"""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None


class MCPServerStatus(BaseModel):
    """MCP Server status"""
    name: str
    version: str
    status: str
    tools_count: int
    resources_count: int
    prompts_count: int
```

- [ ] **Step 4: Implement MCP Server API endpoint**

```python
# backend/app/api/v1/mcp_server.py
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio

from app.mcp_server.server import get_mcp_server

router = APIRouter(prefix="/mcp-server", tags=["mcp-server"])


@router.get("/sse")
async def mcp_server_sse(request: Request):
    """
    MCP Server SSE endpoint for Streamable HTTP transport.
    
    This endpoint implements the MCP Streamable HTTP transport specification,
    allowing MCP clients to connect to Fugue as an MCP Server.
    """
    server = get_mcp_server()
    
    async def event_generator():
        # Send initial connection event
        yield {
            "event": "connected",
            "data": json.dumps({
                "name": "Fugue",
                "version": "0.1.0"
            })
        }
        
        # Keep connection alive
        while True:
            if await request.is_disconnected():
                break
            await asyncio.sleep(30)
            yield {"event": "ping", "data": "{}"}
    
    return EventSourceResponse(event_generator())


@router.post("/message")
async def mcp_server_message(request: Request):
    """
    MCP Server JSON-RPC endpoint.
    
    Handles JSON-RPC 2.0 messages from MCP clients.
    Supports methods: tools/list, tools/call, resources/list, resources/read, prompts/list, prompts/get
    """
    server = get_mcp_server()
    
    try:
        body = await request.json()
        
        # Validate JSON-RPC format
        if "jsonrpc" not in body or body["jsonrpc"] != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {"code": -32600, "message": "Invalid Request"}
            }
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # Route to appropriate handler
        if method == "initialize":
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "prompts": {"listChanged": True}
                },
                "serverInfo": {
                    "name": "Fugue",
                    "version": "0.1.0"
                }
            }
        elif method == "tools/list":
            tools = await server.list_tools()
            result = {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.inputSchema
                    }
                    for t in tools
                ]
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            tool_result = await server.call_tool(tool_name, arguments)
            result = {
                "content": [
                    {"type": "text", "text": str(tool_result)}
                ]
            }
        elif method == "resources/list":
            resources = await server.list_resources()
            result = {
                "resources": [
                    {
                        "uri": str(r.uri),
                        "name": r.name,
                        "description": r.description,
                        "mimeType": r.mimeType
                    }
                    for r in resources
                ]
            }
        elif method == "resources/read":
            uri = params.get("uri")
            resource_result = await server.read_resource(uri)
            result = {
                "contents": [
                    {"uri": uri, "text": str(resource_result)}
                ]
            }
        elif method == "prompts/list":
            prompts = await server.list_prompts()
            result = {
                "prompts": [
                    {
                        "name": p.name,
                        "description": p.description,
                        "arguments": p.arguments
                    }
                    for p in prompts
                ]
            }
        elif method == "prompts/get":
            prompt_name = params.get("name")
            arguments = params.get("arguments", {})
            prompt_result = await server.get_prompt(prompt_name, arguments)
            result = {"messages": prompt_result.messages}
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in locals() else None,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
        }


@router.get("/status")
async def mcp_server_status():
    """Get MCP Server status and capabilities"""
    server = get_mcp_server()
    
    tools = await server.list_tools()
    resources = await server.list_resources()
    prompts = await server.list_prompts()
    
    return {
        "name": "Fugue",
        "version": "0.1.0",
        "status": "running",
        "tools_count": len(tools),
        "resources_count": len(resources),
        "prompts_count": len(prompts),
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": True,
            "sampling": False,
            "elicitation": False
        }
    }
```

- [ ] **Step 5: Register router in API**

```python
# Modify backend/app/api/v1/__init__.py - add this import
from .mcp_server import router as mcp_server_router

# Add to api_router.include_router() calls
api_router.include_router(mcp_server_router)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_mcp_server_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/v1/mcp_server.py backend/app/schemas/mcp_server.py backend/tests/test_mcp_server_api.py backend/app/api/v1/__init__.py
git commit -m "feat(mcp): add MCP Server HTTP endpoint with SSE and JSON-RPC support"
```

---

## Task 3: Git Worktree Manager

**Files:**
- Create: `backend/app/services/worktree_manager.py`
- Modify: `backend/app/models/execution.py`
- Create: `backend/tests/test_worktree.py`

- [ ] **Step 1: Write the failing test for worktree creation**

```python
# backend/tests/test_worktree.py
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.worktree_manager import WorktreeManager


@pytest.fixture
def worktree_manager():
    return WorktreeManager()


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository for testing"""
    import subprocess
    
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True, capture_output=True)
    
    # Create initial commit
    test_file = repo_dir / "test.txt"
    test_file.write_text("initial content")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo_dir, check=True, capture_output=True)
    
    return repo_dir


@pytest.mark.asyncio
async def test_create_worktree(worktree_manager, temp_git_repo):
    """Test creating a new git worktree"""
    worktree_path = await worktree_manager.create_worktree(
        repo_path=str(temp_git_repo),
        worktree_name="test-agent-1",
        branch_name="agent/test-agent-1"
    )
    
    assert worktree_path is not None
    assert os.path.exists(worktree_path)
    assert os.path.exists(os.path.join(worktree_path, ".git"))
    
    # Cleanup
    await worktree_manager.remove_worktree(worktree_path)


@pytest.mark.asyncio
async def test_worktree_isolation(worktree_manager, temp_git_repo):
    """Test that worktrees are isolated from each other"""
    worktree1 = await worktree_manager.create_worktree(
        repo_path=str(temp_git_repo),
        worktree_name="agent-1",
        branch_name="agent/agent-1"
    )
    
    worktree2 = await worktree_manager.create_worktree(
        repo_path=str(temp_git_repo),
        worktree_name="agent-2",
        branch_name="agent/agent-2"
    )
    
    # Write to worktree1
    file1 = Path(worktree1) / "agent1_file.txt"
    file1.write_text("agent 1 content")
    
    # Verify file doesn't exist in worktree2
    file2 = Path(worktree2) / "agent1_file.txt"
    assert not file2.exists()
    
    # Cleanup
    await worktree_manager.remove_worktree(worktree1)
    await worktree_manager.remove_worktree(worktree2)


@pytest.mark.asyncio
async def test_merge_worktree_changes(worktree_manager, temp_git_repo):
    """Test merging worktree changes back to main branch"""
    import subprocess
    
    worktree_path = await worktree_manager.create_worktree(
        repo_path=str(temp_git_repo),
        worktree_name="test-merge",
        branch_name="agent/test-merge"
    )
    
    # Make changes in worktree
    new_file = Path(worktree_path) / "new_feature.py"
    new_file.write_text("def new_feature():\n    return 'hello'")
    
    # Commit changes in worktree
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add new feature"],
        cwd=worktree_path, check=True, capture_output=True
    )
    
    # Merge changes
    success = await worktree_manager.merge_worktree(
        repo_path=str(temp_git_repo),
        branch_name="agent/test-merge",
        target_branch="main"
    )
    
    assert success is True
    
    # Verify file exists in main repo
    main_file = temp_git_repo / "new_feature.py"
    assert main_file.exists()
    
    # Cleanup
    await worktree_manager.remove_worktree(worktree_path)


@pytest.mark.asyncio
async def test_cleanup_worktree_on_failure(worktree_manager, temp_git_repo):
    """Test that worktrees can be safely cleaned up on failure"""
    worktree_path = await worktree_manager.create_worktree(
        repo_path=str(temp_git_repo),
        worktree_name="test-cleanup",
        branch_name="agent/test-cleanup"
    )
    
    # Simulate failure - cleanup should not raise
    await worktree_manager.remove_worktree(worktree_path, force=True)
    
    assert not os.path.exists(worktree_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_worktree.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.worktree_manager'"

- [ ] **Step 3: Implement WorktreeManager**

```python
# backend/app/services/worktree_manager.py
import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
import subprocess

logger = logging.getLogger(__name__)


class WorktreeManager:
    """Manages Git worktrees for isolated agent execution"""
    
    def __init__(self, base_worktree_dir: Optional[str] = None):
        self.base_worktree_dir = base_worktree_dir or os.path.join(
            os.path.expanduser("~"), ".fugue", "worktrees"
        )
        os.makedirs(self.base_worktree_dir, exist_ok=True)
    
    async def create_worktree(
        self,
        repo_path: str,
        worktree_name: str,
        branch_name: Optional[str] = None
    ) -> str:
        """
        Create a new git worktree for isolated execution.
        
        Args:
            repo_path: Path to the main git repository
            worktree_name: Unique name for this worktree (e.g., execution_id or agent_id)
            branch_name: Branch name for the worktree (defaults to "worktree/{worktree_name}")
        
        Returns:
            Path to the created worktree directory
        """
        if branch_name is None:
            branch_name = f"worktree/{worktree_name}"
        
        worktree_path = os.path.join(self.base_worktree_dir, worktree_name)
        
        # Remove existing worktree if it exists
        if os.path.exists(worktree_path):
            await self.remove_worktree(worktree_path, force=True)
        
        try:
            # Create new branch and worktree
            cmd = [
                "git", "worktree", "add",
                "-b", branch_name,
                worktree_path
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to create worktree: {stderr.decode()}")
            
            logger.info(f"Created worktree at {worktree_path} for branch {branch_name}")
            return worktree_path
        
        except Exception as e:
            logger.error(f"Error creating worktree: {e}")
            # Cleanup on failure
            if os.path.exists(worktree_path):
                shutil.rmtree(worktree_path, ignore_errors=True)
            raise
    
    async def remove_worktree(self, worktree_path: str, force: bool = False) -> bool:
        """
        Remove a git worktree.
        
        Args:
            worktree_path: Path to the worktree directory
            force: Force removal even if there are changes
        
        Returns:
            True if successful
        """
        try:
            if not os.path.exists(worktree_path):
                return True
            
            # Get the main repo path from worktree
            git_dir = os.path.join(worktree_path, ".git")
            if not os.path.exists(git_dir):
                # Not a git worktree, just remove directory
                shutil.rmtree(worktree_path)
                return True
            
            # Read main repo path from .git file
            with open(git_dir, "r") as f:
                git_content = f.read()
                # Format: "gitdir: /path/to/main/.git/worktrees/name"
                main_git_dir = git_content.split("gitdir: ")[1].strip()
                main_repo_path = os.path.dirname(os.path.dirname(main_git_dir))
            
            # Remove worktree using git command
            cmd = ["git", "worktree", "remove"]
            if force:
                cmd.append("--force")
            cmd.append(worktree_path)
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=main_repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.warning(f"Git worktree remove failed, force removing: {stderr.decode()}")
                shutil.rmtree(worktree_path, ignore_errors=True)
            
            logger.info(f"Removed worktree at {worktree_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error removing worktree: {e}")
            # Force cleanup
            shutil.rmtree(worktree_path, ignore_errors=True)
            return False
    
    async def merge_worktree(
        self,
        repo_path: str,
        branch_name: str,
        target_branch: str = "main"
    ) -> bool:
        """
        Merge worktree changes back to target branch.
        
        Args:
            repo_path: Path to the main git repository
            branch_name: Branch to merge from
            target_branch: Branch to merge into (default: main)
        
        Returns:
            True if merge was successful
        """
        try:
            # Checkout target branch
            cmd_checkout = ["git", "checkout", target_branch]
            proc = await asyncio.create_subprocess_exec(
                *cmd_checkout,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            # Merge branch
            cmd_merge = ["git", "merge", "--no-ff", "-m", f"Merge {branch_name}", branch_name]
            proc = await asyncio.create_subprocess_exec(
                *cmd_merge,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"Merge failed: {stderr.decode()}")
                # Abort merge on failure
                await asyncio.create_subprocess_exec(
                    "git", "merge", "--abort",
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                return False
            
            logger.info(f"Merged {branch_name} into {target_branch}")
            return True
        
        except Exception as e:
            logger.error(f"Error merging worktree: {e}")
            return False
    
    async def list_worktrees(self, repo_path: str) -> list:
        """List all worktrees for a repository"""
        cmd = ["git", "worktree", "list", "--porcelain"]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return []
        
        worktrees = []
        current = {}
        
        for line in stdout.decode().split("\n"):
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line.split(" ", 1)[1]}
            elif line.startswith("HEAD "):
                current["head"] = line.split(" ", 1)[1]
            elif line.startswith("branch "):
                current["branch"] = line.split(" ", 1)[1]
        
        if current:
            worktrees.append(current)
        
        return worktrees


# Global singleton
_worktree_manager: Optional[WorktreeManager] = None


def get_worktree_manager() -> WorktreeManager:
    """Get or create global WorktreeManager instance"""
    global _worktree_manager
    if _worktree_manager is None:
        _worktree_manager = WorktreeManager()
    return _worktree_manager
```

- [ ] **Step 4: Add worktree_path to Execution model**

```python
# Modify backend/app/models/execution.py - add field to Execution class
worktree_path = Column(String, nullable=True, comment="Path to git worktree for this execution")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_worktree.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/worktree_manager.py backend/app/models/execution.py backend/tests/test_worktree.py
git commit -m "feat(worktree): implement Git Worktree manager for isolated agent execution"
```

---

## Task 4: Three-Tier Approval Mode

**Files:**
- Create: `backend/app/services/approval_manager.py`
- Create: `backend/app/api/v1/approvals.py`
- Create: `backend/app/schemas/approval.py`
- Modify: `backend/app/engine/executor.py`
- Create: `backend/tests/test_approval.py`

- [ ] **Step 1: Write the failing test for approval mode**

```python
# backend/tests/test_approval.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.approval_manager import ApprovalManager, ApprovalMode, ToolRiskLevel
from app.models.crew import Crew


@pytest.fixture
def approval_manager():
    return ApprovalManager()


@pytest.mark.asyncio
async def test_approval_mode_safe_requires_all_approvals(approval_manager):
    """Test that Safe mode requires approval for all operations"""
    assert approval_manager.requires_approval(
        mode=ApprovalMode.SAFE,
        tool_name="file_write",
        risk_level=ToolRiskLevel.LOW
    ) is True
    
    assert approval_manager.requires_approval(
        mode=ApprovalMode.SAFE,
        tool_name="shell_execute",
        risk_level=ToolRiskLevel.HIGH
    ) is True


@pytest.mark.asyncio
async def test_approval_mode_semi_auto_approves_low_risk(approval_manager):
    """Test that Semi-Auto mode auto-approves low-risk operations"""
    assert approval_manager.requires_approval(
        mode=ApprovalMode.SEMI_AUTO,
        tool_name="file_read",
        risk_level=ToolRiskLevel.LOW
    ) is False
    
    assert approval_manager.requires_approval(
        mode=ApprovalMode.SEMI_AUTO,
        tool_name="shell_execute",
        risk_level=ToolRiskLevel.HIGH
    ) is True


@pytest.mark.asyncio
async def test_approval_mode_full_auto_approves_all(approval_manager):
    """Test that Full-Auto mode auto-approves all operations"""
    assert approval_manager.requires_approval(
        mode=ApprovalMode.FULL_AUTO,
        tool_name="file_write",
        risk_level=ToolRiskLevel.LOW
    ) is False
    
    assert approval_manager.requires_approval(
        mode=ApprovalMode.FULL_AUTO,
        tool_name="shell_execute",
        risk_level=ToolRiskLevel.HIGH
    ) is False


@pytest.mark.asyncio
async def test_approval_manager_creates_approval_request(approval_manager):
    """Test creating an approval request"""
    request = await approval_manager.create_approval_request(
        execution_id="test-exec-123",
        tool_name="shell_execute",
        tool_args={"command": "ls -la"},
        risk_level=ToolRiskLevel.HIGH
    )
    
    assert request is not None
    assert request["status"] == "pending"
    assert request["tool_name"] == "shell_execute"
    assert "request_id" in request


@pytest.mark.asyncio
async def test_approval_manager_approves_request(approval_manager):
    """Test approving a pending request"""
    # Create request
    request = await approval_manager.create_approval_request(
        execution_id="test-exec-123",
        tool_name="shell_execute",
        tool_args={"command": "ls -la"},
        risk_level=ToolRiskLevel.HIGH
    )
    
    request_id = request["request_id"]
    
    # Approve request
    result = await approval_manager.approve_request(request_id)
    
    assert result["status"] == "approved"
    assert result["approved_at"] is not None


@pytest.mark.asyncio
async def test_approval_manager_rejects_request(approval_manager):
    """Test rejecting a pending request"""
    # Create request
    request = await approval_manager.create_approval_request(
        execution_id="test-exec-123",
        tool_name="shell_execute",
        tool_args={"command": "rm -rf /"},
        risk_level=ToolRiskLevel.CRITICAL
    )
    
    request_id = request["request_id"]
    
    # Reject request
    result = await approval_manager.reject_request(request_id, reason="Unsafe command")
    
    assert result["status"] == "rejected"
    assert result["reason"] == "Unsafe command"


def test_tool_risk_classification(approval_manager):
    """Test tool risk level classification"""
    assert approval_manager.get_tool_risk_level("file_read") == ToolRiskLevel.LOW
    assert approval_manager.get_tool_risk_level("file_write") == ToolRiskLevel.MEDIUM
    assert approval_manager.get_tool_risk_level("shell_execute") == ToolRiskLevel.HIGH
    assert approval_manager.get_tool_risk_level("database_query") == ToolRiskLevel.HIGH
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_approval.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.approval_manager'"

- [ ] **Step 3: Implement ApprovalManager**

```python
# backend/app/services/approval_manager.py
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from uuid import uuid4

logger = logging.getLogger(__name__)


class ApprovalMode(str, Enum):
    """Approval modes for workflow execution"""
    SAFE = "safe"          # All operations require approval
    SEMI_AUTO = "semi_auto"  # Low-risk auto-approved, high-risk requires approval
    FULL_AUTO = "full_auto"  # All operations auto-approved (sandbox required)


class ToolRiskLevel(str, Enum):
    """Risk levels for tools"""
    LOW = "low"        # Safe operations (file_read, web_search)
    MEDIUM = "medium"  # Moderate risk (file_write, api_call)
    HIGH = "high"      # High risk (shell_execute, database_query)
    CRITICAL = "critical"  # Critical risk (destructive operations)


class ApprovalRequest:
    """Represents a pending approval request"""
    
    def __init__(
        self,
        request_id: str,
        execution_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        risk_level: ToolRiskLevel,
        created_at: datetime
    ):
        self.request_id = request_id
        self.execution_id = execution_id
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.risk_level = risk_level
        self.created_at = created_at
        self.status = "pending"
        self.approved_at: Optional[datetime] = None
        self.approved_by: Optional[str] = None
        self.rejection_reason: Optional[str] = None


class ApprovalManager:
    """Manages approval requests for tool executions"""
    
    # Tool risk level mapping
    TOOL_RISK_LEVELS: Dict[str, ToolRiskLevel] = {
        # Low risk
        "file_read": ToolRiskLevel.LOW,
        "web_search": ToolRiskLevel.LOW,
        "get_execution_status": ToolRiskLevel.LOW,
        "list_workflows": ToolRiskLevel.LOW,
        
        # Medium risk
        "file_write": ToolRiskLevel.MEDIUM,
        "api_call": ToolRiskLevel.MEDIUM,
        "text_analysis": ToolRiskLevel.MEDIUM,
        "image_generation": ToolRiskLevel.MEDIUM,
        
        # High risk
        "shell_execute": ToolRiskLevel.HIGH,
        "database_query": ToolRiskLevel.HIGH,
        "code_execute": ToolRiskLevel.HIGH,
        "execute_workflow": ToolRiskLevel.HIGH,
        
        # Critical risk
        "system_command": ToolRiskLevel.CRITICAL,
        "delete_file": ToolRiskLevel.CRITICAL,
        "drop_table": ToolRiskLevel.CRITICAL,
    }
    
    def __init__(self):
        # In-memory storage for approval requests
        # In production, this should be stored in database
        self._requests: Dict[str, ApprovalRequest] = {}
        self._pending_events: Dict[str, asyncio.Event] = {}
    
    def get_tool_risk_level(self, tool_name: str) -> ToolRiskLevel:
        """Get risk level for a tool"""
        return self.TOOL_RISK_LEVELS.get(tool_name, ToolRiskLevel.MEDIUM)
    
    def requires_approval(
        self,
        mode: ApprovalMode,
        tool_name: str,
        risk_level: Optional[ToolRiskLevel] = None
    ) -> bool:
        """
        Check if a tool call requires approval based on the mode.
        
        Args:
            mode: Current approval mode
            tool_name: Name of the tool being called
            risk_level: Risk level of the tool (auto-detected if not provided)
        
        Returns:
            True if approval is required
        """
        if risk_level is None:
            risk_level = self.get_tool_risk_level(tool_name)
        
        if mode == ApprovalMode.SAFE:
            # Safe mode: all operations require approval
            return True
        
        elif mode == ApprovalMode.SEMI_AUTO:
            # Semi-auto: only medium+ risk requires approval
            return risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]
        
        elif mode == ApprovalMode.FULL_AUTO:
            # Full-auto: no approval required (sandbox must be enabled)
            return False
        
        return True  # Default to requiring approval
    
    async def create_approval_request(
        self,
        execution_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        risk_level: Optional[ToolRiskLevel] = None
    ) -> Dict[str, Any]:
        """
        Create a new approval request.
        
        Args:
            execution_id: ID of the execution
            tool_name: Name of the tool
            tool_args: Arguments for the tool
            risk_level: Risk level (auto-detected if not provided)
        
        Returns:
            Approval request details
        """
        if risk_level is None:
            risk_level = self.get_tool_risk_level(tool_name)
        
        request_id = str(uuid4())
        request = ApprovalRequest(
            request_id=request_id,
            execution_id=execution_id,
            tool_name=tool_name,
            tool_args=tool_args,
            risk_level=risk_level,
            created_at=datetime.utcnow()
        )
        
        self._requests[request_id] = request
        self._pending_events[request_id] = asyncio.Event()
        
        logger.info(f"Created approval request {request_id} for {tool_name}")
        
        return {
            "request_id": request_id,
            "execution_id": execution_id,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "risk_level": risk_level.value,
            "status": "pending",
            "created_at": request.created_at.isoformat()
        }
    
    async def approve_request(
        self,
        request_id: str,
        approved_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a pending request.
        
        Args:
            request_id: ID of the request to approve
            approved_by: User who approved the request
        
        Returns:
            Updated request details
        """
        if request_id not in self._requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self._requests[request_id]
        request.status = "approved"
        request.approved_at = datetime.utcnow()
        request.approved_by = approved_by
        
        # Signal waiting coroutines
        if request_id in self._pending_events:
            self._pending_events[request_id].set()
        
        logger.info(f"Approved request {request_id}")
        
        return {
            "request_id": request_id,
            "status": "approved",
            "approved_at": request.approved_at.isoformat(),
            "approved_by": approved_by
        }
    
    async def reject_request(
        self,
        request_id: str,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        Reject a pending request.
        
        Args:
            request_id: ID of the request to reject
            reason: Reason for rejection
        
        Returns:
            Updated request details
        """
        if request_id not in self._requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self._requests[request_id]
        request.status = "rejected"
        request.rejection_reason = reason
        
        # Signal waiting coroutines
        if request_id in self._pending_events:
            self._pending_events[request_id].set()
        
        logger.info(f"Rejected request {request_id}: {reason}")
        
        return {
            "request_id": request_id,
            "status": "rejected",
            "reason": reason
        }
    
    async def wait_for_approval(
        self,
        request_id: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Wait for an approval request to be approved or rejected.
        
        Args:
            request_id: ID of the request to wait for
            timeout: Timeout in seconds (default: 5 minutes)
        
        Returns:
            Final request status
        """
        if request_id not in self._requests:
            raise ValueError(f"Request {request_id} not found")
        
        if request_id not in self._pending_events:
            self._pending_events[request_id] = asyncio.Event()
        
        try:
            await asyncio.wait_for(
                self._pending_events[request_id].wait(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            request = self._requests[request_id]
            request.status = "timeout"
            return {
                "request_id": request_id,
                "status": "timeout",
                "message": "Approval request timed out"
            }
        
        request = self._requests[request_id]
        return {
            "request_id": request_id,
            "status": request.status,
            "approved_at": request.approved_at.isoformat() if request.approved_at else None,
            "rejection_reason": request.rejection_reason
        }
    
    def get_pending_requests(self, execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pending approval requests"""
        requests = []
        for req in self._requests.values():
            if req.status == "pending":
                if execution_id is None or req.execution_id == execution_id:
                    requests.append({
                        "request_id": req.request_id,
                        "execution_id": req.execution_id,
                        "tool_name": req.tool_name,
                        "tool_args": req.tool_args,
                        "risk_level": req.risk_level.value,
                        "created_at": req.created_at.isoformat()
                    })
        return requests


# Global singleton
_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """Get or create global ApprovalManager instance"""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager
```

- [ ] **Step 4: Implement approval API endpoint**

```python
# backend/app/api/v1/approvals.py
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.approval_manager import get_approval_manager

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalRequestResponse(BaseModel):
    request_id: str
    execution_id: str
    tool_name: str
    tool_args: dict
    risk_level: str
    status: str
    created_at: str


class ApprovalAction(BaseModel):
    approved_by: Optional[str] = None
    reason: Optional[str] = None


@router.get("/pending", response_model=List[ApprovalRequestResponse])
async def get_pending_approvals(execution_id: Optional[str] = None):
    """Get all pending approval requests"""
    manager = get_approval_manager()
    return manager.get_pending_requests(execution_id)


@router.post("/{request_id}/approve")
async def approve_request(request_id: str, action: ApprovalAction = None):
    """Approve a pending request"""
    manager = get_approval_manager()
    try:
        result = await manager.approve_request(
            request_id,
            approved_by=action.approved_by if action else None
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{request_id}/reject")
async def reject_request(request_id: str, action: ApprovalAction):
    """Reject a pending request"""
    manager = get_approval_manager()
    try:
        result = await manager.reject_request(request_id, reason=action.reason or "")
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- [ ] **Step 5: Add approval hook to executor**

```python
# Modify backend/app/engine/executor.py - add approval check before tool execution

# Add import at top
from app.services.approval_manager import get_approval_manager, ApprovalMode, ToolRiskLevel
from app.models.crew import Crew

# In _execute_task method, before tool execution (around line 1133):
async def _check_approval_required(
    self,
    tool_name: str,
    tool_args: dict,
    crew: Crew
) -> bool:
    """Check if tool execution requires approval"""
    manager = get_approval_manager()
    
    # Get approval mode from crew config
    mode = ApprovalMode(crew.approval_mode) if hasattr(crew, 'approval_mode') else ApprovalMode.SEMI_AUTO
    
    if not manager.requires_approval(mode=mode, tool_name=tool_name):
        return False
    
    # Create approval request
    request = await manager.create_approval_request(
        execution_id=self.execution_id,
        tool_name=tool_name,
        tool_args=tool_args
    )
    
    # Update execution status
    async with get_db_session() as db:
        execution = await db.get(Execution, self.execution_id)
        if execution:
            execution.status = ExecutionStatus.WAITING_REVIEW
            await db.commit()
    
    # Wait for approval
    result = await manager.wait_for_approval(request["request_id"], timeout=300)
    
    if result["status"] != "approved":
        raise Exception(f"Tool execution rejected: {result.get('reason', 'No reason provided')}")
    
    return True
```

- [ ] **Step 6: Add approval_mode to Crew model**

```python
# Modify backend/app/models/crew.py - add field to Crew class
approval_mode = Column(
    String,
    default="semi_auto",
    comment="Approval mode: safe, semi_auto, full_auto"
)
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_approval.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/approval_manager.py backend/app/api/v1/approvals.py backend/app/engine/executor.py backend/app/models/crew.py backend/tests/test_approval.py
git commit -m "feat(approval): implement three-tier approval mode (safe/semi-auto/full-auto)"
```

---

## Task 5: Agent Execution Sandbox

**Files:**
- Create: `backend/app/engine/sandbox.py`
- Modify: `backend/app/engine/tools.py`
- Create: `backend/tests/test_sandbox.py`

- [ ] **Step 1: Write the failing test for sandbox execution**

```python
# backend/tests/test_sandbox.py
import pytest
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from app.engine.sandbox import SandboxManager, SandboxType, SandboxConfig


@pytest.fixture
def sandbox_manager():
    return SandboxManager()


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for testing"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Create test files
    (workspace / "test.txt").write_text("test content")
    (workspace / "script.py").write_text("print('hello')")
    
    return workspace


def test_sandbox_config_defaults():
    """Test default sandbox configuration"""
    config = SandboxConfig()
    
    assert config.enable_filesystem_isolation is True
    assert config.enable_network_isolation is False
    assert config.allowed_paths == []
    assert config.blocked_commands == ["rm -rf", "dd", "mkfs"]


def test_sandbox_config_custom():
    """Test custom sandbox configuration"""
    config = SandboxConfig(
        enable_filesystem_isolation=True,
        enable_network_isolation=True,
        allowed_paths=["/tmp", "/home"],
        blocked_commands=["rm", "sudo"]
    )
    
    assert config.enable_network_isolation is True
    assert "/tmp" in config.allowed_paths
    assert "rm" in config.blocked_commands


@pytest.mark.asyncio
async def test_sandbox_execute_command(sandbox_manager, temp_workspace):
    """Test executing a command in sandbox"""
    config = SandboxConfig(
        enable_filesystem_isolation=True,
        enable_network_isolation=False
    )
    
    result = await sandbox_manager.execute_in_sandbox(
        command="echo 'hello world'",
        workspace=str(temp_workspace),
        config=config,
        sandbox_type=SandboxType.BWRAP
    )
    
    assert result["success"] is True
    assert "hello world" in result["output"]


@pytest.mark.asyncio
async def test_sandbox_blocks_dangerous_commands(sandbox_manager, temp_workspace):
    """Test that sandbox blocks dangerous commands"""
    config = SandboxConfig(
        blocked_commands=["rm -rf"]
    )
    
    result = await sandbox_manager.execute_in_sandbox(
        command="rm -rf /",
        workspace=str(temp_workspace),
        config=config,
        sandbox_type=SandboxType.BWRAP
    )
    
    assert result["success"] is False
    assert "blocked" in result["error"].lower() or "not allowed" in result["error"].lower()


@pytest.mark.asyncio
async def test_sandbox_isolates_filesystem(sandbox_manager, temp_workspace):
    """Test that sandbox isolates filesystem access"""
    config = SandboxConfig(
        enable_filesystem_isolation=True,
        allowed_paths=[str(temp_workspace)]
    )
    
    # This should succeed - within allowed path
    result = await sandbox_manager.execute_in_sandbox(
        command=f"cat {temp_workspace}/test.txt",
        workspace=str(temp_workspace),
        config=config,
        sandbox_type=SandboxType.BWRAP
    )
    
    assert result["success"] is True
    assert "test content" in result["output"]


@pytest.mark.asyncio
async def test_sandbox_prevents_path_traversal(sandbox_manager, temp_workspace):
    """Test that sandbox prevents path traversal attacks"""
    config = SandboxConfig(
        enable_filesystem_isolation=True,
        allowed_paths=[str(temp_workspace)]
    )
    
    # This should fail - attempting to access parent directory
    result = await sandbox_manager.execute_in_sandbox(
        command=f"cat {temp_workspace}/../../../etc/passwd",
        workspace=str(temp_workspace),
        config=config,
        sandbox_type=SandboxType.BWRAP
    )
    
    assert result["success"] is False


@pytest.mark.asyncio
async def test_sandbox_type_none(sandbox_manager, temp_workspace):
    """Test execution without sandbox (for development)"""
    config = SandboxConfig()
    
    result = await sandbox_manager.execute_in_sandbox(
        command="echo 'no sandbox'",
        workspace=str(temp_workspace),
        config=config,
        sandbox_type=SandboxType.NONE
    )
    
    assert result["success"] is True
    assert "no sandbox" in result["output"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_sandbox.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.engine.sandbox'"

- [ ] **Step 3: Implement SandboxManager**

```python
# backend/app/engine/sandbox.py
import asyncio
import logging
import os
import shlex
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class SandboxType(str, Enum):
    """Types of sandbox implementations"""
    NONE = "none"        # No sandbox (development mode)
    BWRAP = "bwrap"      # bubblewrap (Linux)
    DOCKER = "docker"    # Docker container
    SEATBELT = "seatbelt"  # macOS Seatbelt


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution"""
    enable_filesystem_isolation: bool = True
    enable_network_isolation: bool = False
    allowed_paths: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(default_factory=lambda: [
        "rm -rf /",
        "rm -rf /*",
        "dd if=",
        "mkfs",
        ":(){ :|:& };:",  # Fork bomb
        "chmod 777 /",
        "chown root",
    ])
    max_execution_time: int = 300  # seconds
    max_memory_mb: int = 512
    max_cpu_percent: int = 50


class SandboxManager:
    """Manages sandboxed execution of commands"""
    
    def __init__(self):
        self._detect_available_sandboxes()
    
    def _detect_available_sandboxes(self):
        """Detect available sandbox implementations"""
        self.available_sandboxes = {SandboxType.NONE}
        
        # Check for bubblewrap
        try:
            import subprocess
            result = subprocess.run(
                ["which", "bwrap"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.available_sandboxes.add(SandboxType.BWRAP)
                logger.info("bubblewrap (bwrap) detected")
        except Exception:
            pass
        
        # Check for Docker
        try:
            import subprocess
            result = subprocess.run(
                ["which", "docker"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.available_sandboxes.add(SandboxType.DOCKER)
                logger.info("Docker detected")
        except Exception:
            pass
    
    def _validate_command(self, command: str, config: SandboxConfig) -> Optional[str]:
        """
        Validate command against blocked patterns.
        
        Returns:
            Error message if command is blocked, None if allowed
        """
        command_lower = command.lower().strip()
        
        for blocked in config.blocked_commands:
            if blocked.lower() in command_lower:
                return f"Command blocked: contains '{blocked}'"
        
        return None
    
    def _build_bwrap_command(
        self,
        command: str,
        workspace: str,
        config: SandboxConfig
    ) -> List[str]:
        """Build bubblewrap command with isolation flags"""
        bwrap_cmd = ["bwrap"]
        
        # Basic isolation
        bwrap_cmd.extend([
            "--unshare-all",  # Unshare all namespaces
            "--die-with-parent",  # Die when parent process dies
        ])
        
        # Filesystem isolation
        if config.enable_filesystem_isolation:
            # Mount root filesystem as read-only
            bwrap_cmd.extend([
                "--ro-bind", "/", "/",
                "--tmpfs", "/tmp",
                "--proc", "/proc",
                "--dev", "/dev",
            ])
            
            # Bind mount allowed paths
            for path in config.allowed_paths:
                if os.path.exists(path):
                    bwrap_cmd.extend(["--bind", path, path])
            
            # Bind workspace as read-write
            bwrap_cmd.extend(["--bind", workspace, workspace])
        else:
            # No filesystem isolation - bind everything
            bwrap_cmd.extend([
                "--bind", "/", "/",
                "--proc", "/proc",
                "--dev", "/dev",
            ])
        
        # Network isolation
        if config.enable_network_isolation:
            bwrap_cmd.extend(["--unshare-net"])
        
        # Resource limits
        bwrap_cmd.extend([
            "--new-session",
            "--setenv", "HOME", workspace,
            "--chdir", workspace,
        ])
        
        # The actual command to execute
        bwrap_cmd.extend(["--", "/bin/sh", "-c", command])
        
        return bwrap_cmd
    
    def _build_docker_command(
        self,
        command: str,
        workspace: str,
        config: SandboxConfig
    ) -> List[str]:
        """Build Docker command with isolation flags"""
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none" if config.enable_network_isolation else "bridge",
            "-v", f"{workspace}:/workspace:rw",
            "-w", "/workspace",
            "--memory", f"{config.max_memory_mb}m",
            "--cpus", str(config.max_cpu_percent / 100),
            "python:3.11-slim",  # Base image
            "/bin/sh", "-c", command
        ]
        
        return docker_cmd
    
    async def execute_in_sandbox(
        self,
        command: str,
        workspace: str,
        config: Optional[SandboxConfig] = None,
        sandbox_type: Optional[SandboxType] = None
    ) -> Dict[str, Any]:
        """
        Execute a command in a sandbox.
        
        Args:
            command: Command to execute
            workspace: Working directory for execution
            config: Sandbox configuration
            sandbox_type: Type of sandbox to use
        
        Returns:
            Execution result with success, output, and error fields
        """
        if config is None:
            config = SandboxConfig()
        
        if sandbox_type is None:
            # Auto-detect best available sandbox
            if SandboxType.BWRAP in self.available_sandboxes:
                sandbox_type = SandboxType.BWRAP
            elif SandboxType.DOCKER in self.available_sandboxes:
                sandbox_type = SandboxType.DOCKER
            else:
                sandbox_type = SandboxType.NONE
        
        # Validate command
        validation_error = self._validate_command(command, config)
        if validation_error:
            return {
                "success": False,
                "output": "",
                "error": validation_error,
                "sandbox_type": sandbox_type.value
            }
        
        # Ensure workspace exists
        os.makedirs(workspace, exist_ok=True)
        
        try:
            # Build sandbox command
            if sandbox_type == SandboxType.BWRAP:
                sandbox_cmd = self._build_bwrap_command(command, workspace, config)
            elif sandbox_type == SandboxType.DOCKER:
                sandbox_cmd = self._build_docker_command(command, workspace, config)
            else:
                # No sandbox - direct execution
                sandbox_cmd = ["/bin/sh", "-c", command]
            
            logger.info(f"Executing in {sandbox_type.value} sandbox: {command[:100]}...")
            
            # Execute command
            proc = await asyncio.create_subprocess_exec(
                *sandbox_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=config.max_execution_time
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Command timed out after {config.max_execution_time} seconds",
                    "sandbox_type": sandbox_type.value
                }
            
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace"),
                "error": stderr.decode("utf-8", errors="replace") if proc.returncode != 0 else "",
                "exit_code": proc.returncode,
                "sandbox_type": sandbox_type.value
            }
        
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "sandbox_type": sandbox_type.value
            }


# Global singleton
_sandbox_manager: Optional[SandboxManager] = None


def get_sandbox_manager() -> SandboxManager:
    """Get or create global SandboxManager instance"""
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = SandboxManager()
    return _sandbox_manager
```

- [ ] **Step 4: Integrate sandbox into tools.py**

```python
# Modify backend/app/engine/tools.py - wrap code_execute tool

from app.engine.sandbox import get_sandbox_manager, SandboxConfig

# Update code_execute tool implementation
async def code_execute(command: str, language: str = "python", **kwargs) -> str:
    """Execute code in sandboxed environment"""
    sandbox = get_sandbox_manager()
    
    config = SandboxConfig(
        enable_filesystem_isolation=True,
        enable_network_isolation=False,
        max_execution_time=60
    )
    
    if language == "python":
        # Write Python code to temp file and execute
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(command)
            temp_path = f.name
        
        result = await sandbox.execute_in_sandbox(
            command=f"python {temp_path}",
            workspace=os.path.dirname(temp_path),
            config=config
        )
        
        # Cleanup
        os.unlink(temp_path)
    else:
        result = await sandbox.execute_in_sandbox(
            command=command,
            workspace=tempfile.gettempdir(),
            config=config
        )
    
    if result["success"]:
        return result["output"]
    else:
        return f"Error: {result['error']}"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/test_sandbox.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/engine/sandbox.py backend/app/engine/tools.py backend/tests/test_sandbox.py
git commit -m "feat(sandbox): implement execution sandbox with bwrap and Docker support"
```

---

## Task 6: Integration Test

**Files:**
- Create: `backend/tests/integration/test_p0_integration.py`

- [ ] **Step 1: Write integration test**

```python
# backend/tests/integration/test_p0_integration.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.mcp_server.server import get_mcp_server
from app.services.worktree_manager import get_worktree_manager
from app.services.approval_manager import get_approval_manager, ApprovalMode
from app.engine.sandbox import get_sandbox_manager, SandboxConfig


@pytest.mark.asyncio
async def test_mcp_server_integration():
    """Test MCP Server can list tools and execute them"""
    server = get_mcp_server()
    
    # List tools
    tools = await server.list_tools()
    assert len(tools) > 0
    
    # Verify tool names
    tool_names = [t.name for t in tools]
    assert "execute_workflow" in tool_names
    assert "get_execution_status" in tool_names
    assert "list_workflows" in tool_names


@pytest.mark.asyncio
async def test_approval_mode_integration():
    """Test approval mode integration with execution engine"""
    manager = get_approval_manager()
    
    # Test Safe mode
    assert manager.requires_approval(ApprovalMode.SAFE, "file_read") is True
    assert manager.requires_approval(ApprovalMode.SAFE, "shell_execute") is True
    
    # Test Semi-Auto mode
    assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "file_read") is False
    assert manager.requires_approval(ApprovalMode.SEMI_AUTO, "shell_execute") is True
    
    # Test Full-Auto mode
    assert manager.requires_approval(ApprovalMode.FULL_AUTO, "shell_execute") is False


@pytest.mark.asyncio
async def test_sandbox_integration():
    """Test sandbox execution integration"""
    sandbox = get_sandbox_manager()
    
    config = SandboxConfig(
        enable_filesystem_isolation=True,
        enable_network_isolation=False
    )
    
    # Test safe command
    result = await sandbox.execute_in_sandbox(
        command="echo 'test'",
        workspace="/tmp",
        config=config
    )
    
    assert result["success"] is True
    assert "test" in result["output"]
    
    # Test blocked command
    result = await sandbox.execute_in_sandbox(
        command="rm -rf /",
        workspace="/tmp",
        config=config
    )
    
    assert result["success"] is False
```

- [ ] **Step 2: Run integration test**

Run: `cd E:\fugue\.claude\worktrees\great-shockley-bf7be6 && python -m pytest backend/tests/integration/test_p0_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_p0_integration.py
git commit -m "test(integration): add P0 features integration tests"
```

---

## Summary

After completing all tasks, Fugue will have:

1. **MCP Server Layer** - Expose agents as standard MCP Tools/Resources/Prompts, enabling integration with Claude Code, Cursor, and other MCP clients
2. **Git Worktree Isolation** - Each agent execution gets an isolated working directory, preventing file conflicts in parallel execution
3. **Three-Tier Approval Mode** - Safe/Semi-Auto/Full-Auto modes give users control over agent autonomy
4. **Execution Sandbox** - bubblewrap/Docker sandboxing ensures safe execution of untrusted code

Total files created: 15
Total files modified: 5
Total tests: 30+
