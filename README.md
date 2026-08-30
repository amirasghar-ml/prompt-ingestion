# Prompt Ingestion

A lightweight Python service for **ingesting, storing, versioning, and serving AI prompts** from multiple sources.

## Features

| Feature | Detail |
|---|---|
| **Multi-source ingestion** | Direct API, file upload (.json / .jsonl / .csv / .txt / .md), bulk JSON body |
| **CRUD** | Create, read, update, delete prompts via REST API |
| **Versioning** | Every content edit creates an immutable version snapshot |
| **Tagging & Categories** | Many-to-many tags, free-form categories |
| **Full-text search** | Filter by query, category, tag, source, active status |
| **Audit logs** | Every ingestion run is logged with counts and error details |
| **Web UI** | Built-in dashboard to browse, search, create, and ingest prompts |
| **OpenAPI docs** | Auto-generated Swagger UI at `/api/docs` |

## Quick Start

```bash
# 1. Activate the virtual environment
.\env\Scripts\Activate.ps1          # Windows PowerShell
# or
source env/bin/activate              # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) configure environment
copy .env.example .env               # Windows
# cp .env.example .env               # macOS / Linux

# 4. Start the server
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** for the web dashboard, or **http://localhost:8000/api/docs** for the Swagger UI.

## Project Structure

```
prompt-ingestion/
├── app/
│   ├── main.py           # FastAPI app & startup
│   ├── database.py       # SQLAlchemy engine & session
│   ├── models.py         # ORM models (Prompt, Tag, PromptVersion, IngestionLog)
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── crud.py           # Database access helpers
│   ├── routers/
│   │   ├── prompts.py    # CRUD & search endpoints
│   │   └── ingest.py     # Ingestion endpoints + audit logs
│   └── ingestion/
│       ├── parsers.py    # File parsers (JSON / JSONL / CSV / TXT / MD)
│       └── engine.py     # Core ingestion engine (upsert logic)
├── static/
│   └── index.html        # Web dashboard (vanilla JS, no build step)
├── requirements.txt
├── .env.example
└── README.md
```

## API Reference

### Prompts

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/prompts/` | List / search prompts (paginated) |
| `POST` | `/api/prompts/` | Create a single prompt |
| `GET` | `/api/prompts/{id}` | Get prompt by ID |
| `PUT` | `/api/prompts/{id}` | Update prompt (bumps version if content changes) |
| `DELETE` | `/api/prompts/{id}` | Delete prompt |
| `GET` | `/api/prompts/{id}/versions` | Get all version snapshots |
| `GET` | `/api/prompts/stats` | Aggregate statistics |
| `GET` | `/api/prompts/tags` | List all tags |

### Ingestion

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/ingest/bulk` | Bulk ingest from JSON body |
| `POST` | `/api/ingest/file` | Ingest from uploaded file |
| `GET` | `/api/ingest/logs` | List ingestion audit logs |

### Query Parameters (`GET /api/prompts/`)

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Full-text search (name, content, description) |
| `category` | string | Filter by category (partial match) |
| `tags` | string[] | Filter by tag names (AND logic) |
| `is_active` | bool | Filter active/inactive prompts |
| `source` | string | Filter by ingestion source |
| `skip` | int | Pagination offset |
| `limit` | int | Page size (max 200) |

## Supported File Formats

| Format | Structure |
|--------|-----------|
| `.json` | Array of `{name, content, description?, category?, tags?}` objects, or `{"prompts": [...]}` |
| `.jsonl` | One JSON object per line |
| `.csv` | Columns: `name`, `content`, `description`, `category`, `tags` (comma-sep inside cell) |
| `.txt` / `.md` | Entire file becomes `content`; filename becomes `name` |

## Example: Bulk Ingest via curl

```bash
curl -X POST http://localhost:8000/api/ingest/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "prompts": [
      {
        "name": "Summarise Text",
        "content": "Summarise the following:\n\n{{text}}",
        "category": "utility",
        "tags": ["summarise", "gpt"]
      }
    ],
    "overwrite_existing": false
  }'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./prompts.db` | SQLAlchemy DB URL |
