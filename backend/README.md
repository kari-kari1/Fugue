# Fugue Backend

FastAPI backend for the Fugue multi-agent workflow platform.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## API Documentation

After starting the server, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
