# Fugue

[![CI](https://github.com/kari-kari1/Fugue/actions/workflows/ci.yml/badge.svg)](https://github.com/kari-kari1/Fugue/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/kari-kari1/Fugue)](https://github.com/kari-kari1/Fugue/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Multi-agent workflow orchestration platform.** Design agents and tasks on a visual DAG canvas, execute them with a powerful orchestration engine, and observe every thought and tool call in real time.

[中文文档](README_zh.md)

---

## Features

**Orchestration**
- Visual DAG editor with 13 node types -- Agent, Task, Condition, Loop, Human Review, 5 Workflow Patterns, 3 Event Flow nodes
- 4 process modes: sequential, parallel, orchestrator-workers, event-driven
- Iteration refinement -- submit feedback to regenerate outputs with full context chain

**Intelligence**
- Multi-provider LLM support (OpenAI, Anthropic, Google, Ollama, custom endpoints)
- Knowledge base with document upload, chunking, and semantic vector search
- Agent long-term memory with composite scoring (recency + semantic + importance)

**Observability**
- WebSocket real-time stream of agent thinking, tool calls, token usage, and cost
- Execution trace with per-task timeline and checkpoint snapshots

**Platform**
- MCP Server (JSON-RPC + SSE) exposing agents as callable tools
- Plugin marketplace with runtime install/uninstall
- Webhook notifications with HMAC-SHA256 signing
- Cron-based scheduled executions
- REST API publishing for external integration

**Security**
- Three-tier approval mode: safe, semi-auto, full-auto
- Execution sandbox with filesystem and network isolation (bubblewrap / Docker)
- Git worktree isolation for concurrent executions
- JWT authentication with RBAC (admin / user)
- Security headers middleware, rate limiting

**Desktop**
- Tauri (Rust) desktop app with native filesystem access
- Bundled backend sidecar -- no separate server needed
- Windows installer available in [Releases](https://github.com/kari-kari1/Fugue/releases)

## Quick Start

### Desktop App

Download `Fugue_0.1.0_x64-setup.exe` from [Releases](https://github.com/kari-kari1/Fugue/releases). The installer bundles everything -- just run it.

### Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Frontend: `http://localhost:3000` | API: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

### Local Development

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Desktop dev mode
npm run tauri dev
```

## Architecture

```
                    ┌─────────────────────────┐
                    │    React + ReactFlow     │
                    │    Visual DAG Editor     │
                    └────────┬────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         REST API      WebSocket       Tauri IPC
         (FastAPI)     (real-time)    (local-fs)
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────┴────────────────┐
                    │    Execution Engine      │
                    │  ┌───────────────────┐  │
                    │  │ Sequential        │  │
                    │  │ Parallel          │  │
                    │  │ Orchestrator      │  │
                    │  │ Event Flow        │  │
                    │  └───────────────────┘  │
                    │                          │
                    │  LLM ─── Tools ─── RAG   │
                    │  Memory ── Sandbox ── Git │
                    └──────────────────────────┘
```

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 19, TypeScript 5, Vite 6, ReactFlow 12, Zustand 5, Tailwind CSS 4 |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, LiteLLM |
| Desktop | Tauri 2 (Rust), WebView2 |
| Data | SQLite (desktop) / PostgreSQL (server), ChromaDB (vector) |
| Optional | Redis, Celery, MinIO |

## Project Structure

```
Fugue/
├── backend/
│   ├── app/
│   │   ├── api/v1/          146 REST endpoints
│   │   ├── engine/          execution engine, flow executor, sandbox
│   │   ├── models/          21 SQLAlchemy models
│   │   ├── services/        memory, vector store, webhooks, templates
│   │   ├── mcp_server/      MCP Server (JSON-RPC + SSE)
│   │   └── plugins/         plugin SDK and built-in plugins
│   ├── tests/               299 test cases
│   ├── alembic/             database migrations
│   └── fugue.spec           PyInstaller packaging
├── frontend/
│   ├── src/
│   │   ├── pages/           14 pages
│   │   ├── components/      ReactFlow nodes, editor panels
│   │   ├── stores/          Zustand state management
│   │   └── api/             API client layer
│   ├── src-tauri/           Tauri desktop (Rust)
│   └── e2e/                 Playwright E2E tests
├── docs/                    design specs, deployment guide
├── scripts/                 security audit script
└── docker-compose.yml
```

## Testing

```bash
cd backend && pytest tests/ -v          # 299 tests
cd frontend && npx tsc --noEmit         # type check
cd frontend && npm run build            # production build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push and open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)
