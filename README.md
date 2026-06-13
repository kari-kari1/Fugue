# Fugue

[![CI](https://github.com/kari-kari1/Fugue/actions/workflows/ci.yml/badge.svg)](https://github.com/kari-kari1/Fugue/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/kari-kari1/Fugue)](https://github.com/kari-kari1/Fugue/releases)

**Multi-agent workflow orchestration platform.**

Fugue transforms complex multi-agent collaboration into visual, reusable, monitorable workflows. Design agents and tasks on a DAG canvas, execute them with a powerful orchestration engine, and observe every thought and tool call in real time.

## Highlights

- **Visual DAG Editor** -- drag-and-drop 13 node types: Agent, Task, Condition, Loop, Human Review, 5 Workflow Patterns, 3 Event Flow nodes
- **Execution Engine** -- sequential, parallel, orchestrator-workers, and event-driven process modes
- **Real-time Monitoring** -- WebSocket stream of agent thinking, tool calls, cost and token usage
- **Knowledge Base** -- document upload with chunking and vector search (ChromaDB, with SQLite fallback)
- **Agent Memory** -- long-term cross-execution memory with composite scoring (recency + semantic + importance)
- **Iteration Refinement** -- submit feedback to refine outputs with full context chain
- **MCP Server** -- expose agents as tools via JSON-RPC + SSE transport
- **Plugin Marketplace** -- install, uninstall, enable/disable plugins at runtime
- **Webhook & Scheduling** -- HMAC-SHA256 signed webhooks, cron-based scheduled executions
- **Three-Tier Approval** -- safe, semi-auto, and full-auto execution modes with risk classification
- **Execution Sandbox** -- filesystem and network isolation via bubblewrap / Docker
- **Git Worktree Isolation** -- concurrent executions in isolated working directories
- **Desktop App** -- Tauri (Rust) wrapper with native filesystem access

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 19, TypeScript, Vite 6, ReactFlow 12, Zustand 5, Tailwind CSS 4 |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, LiteLLM |
| Desktop | Tauri 2 (Rust), WebView2 |
| Database | SQLite (desktop) / PostgreSQL (server) |
| Optional | Redis, ChromaDB, Celery, MinIO |

## Quick Start

### Desktop App (recommended)

Download the installer from [Releases](https://github.com/kari-kari1/Fugue/releases), then run `Fugue_0.1.0_x64-setup.exe`. The app bundles a backend sidecar -- no additional setup required.

### Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### Local Development

**Backend:**

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Tauri Desktop (dev mode):**

```bash
npm run tauri dev
```

## Project Structure

```
Fugue/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # 146 REST endpoints
│   │   ├── engine/          # Execution engine, flow executor, sandbox
│   │   ├── models/          # 21 SQLAlchemy models
│   │   ├── services/        # Memory, vector store, webhooks, templates
│   │   ├── mcp_server/      # MCP Server (JSON-RPC + SSE)
│   │   └── plugins/         # Plugin SDK and built-in plugins
│   ├── tests/               # 299 test cases
│   ├── alembic/             # Database migrations
│   └── fugue.spec           # PyInstaller packaging
├── frontend/
│   ├── src/
│   │   ├── pages/           # 14 pages (Dashboard, Editor, Execution, ...)
│   │   ├── components/      # ReactFlow nodes, editor panels, motion
│   │   ├── stores/          # Zustand state management
│   │   └── api/             # API client layer
│   ├── src-tauri/           # Tauri desktop (Rust)
│   └── e2e/                 # Playwright E2E tests
├── docs/                    # Design specs, deployment guide, security checklist
├── scripts/                 # Security audit script
└── docker-compose.yml
```

## Configuration

Copy `backend/.env.example` to `backend/.env` and set:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | JWT signing key (auto-generated if empty) | Yes |
| `DATABASE_URL` | SQLAlchemy connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key | For OpenAI models |
| `ANTHROPIC_API_KEY` | Anthropic API key | For Claude models |
| `GOOGLE_API_KEY` | Google API key | For Gemini models |
| `REDIS_URL` | Redis connection string | Optional |
| `LOCAL_FS_PORT` | Tauri local filesystem port | Auto-set by desktop app |

## Testing

```bash
cd backend && pytest tests/ -v
cd frontend && npx tsc --noEmit && npm run build
```

## Architecture

```
User Canvas (ReactFlow)
        |
        v
  REST API (FastAPI)  <--->  WebSocket (real-time events)
        |
        v
  Execution Engine
  ├── Sequential / Parallel / Orchestrator / Event Flow
  ├── LLM calls (LiteLLM -- OpenAI / Anthropic / Google / Ollama)
  ├── Tool system (built-in + MCP + plugins)
  ├── Knowledge base RAG (ChromaDB / SQLite fallback)
  ├── Agent memory (short-term + long-term composite scoring)
  └── Sandbox (bubblewrap / Docker isolation)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push and open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

[MIT](LICENSE)
