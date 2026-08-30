import json
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.ingestion.engine import ingest_items
from app.ingestion.parsers import parse_file

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/bulk", response_model=schemas.IngestionResult, status_code=status.HTTP_200_OK)
def ingest_bulk_json(
    payload: schemas.BulkIngestRequest,
    db: Session = Depends(get_db),
):
    """
    Ingest an array of prompts from a JSON request body.
    Use `overwrite_existing: true` to update prompts that share a name.
    """
    items = [p.dict() for p in payload.prompts]
    return ingest_items(
        db,
        items,
        source_type="bulk_json",
        source_name="api-body",
        overwrite_existing=payload.overwrite_existing,
    )


@router.post("/file", response_model=schemas.IngestionResult, status_code=status.HTTP_200_OK)
async def ingest_file(
    file: UploadFile = File(..., description="Upload a .json, .jsonl, .csv, .txt, or .md file"),
    overwrite_existing: bool = Form(False),
    default_category: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Upload a file containing one or more prompts.

    Supported formats:
    - **JSON** – array of `{name, content, description?, category?, tags?}` objects
    - **JSONL** – one JSON object per line
    - **CSV** – columns: `name`, `content`, `description`, `category`, `tags`
    - **TXT / MD** – entire file becomes the `content` of a single prompt (filename → name)
    """
    raw = await file.read()
    try:
        items = parse_file(raw, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if default_category:
        for item in items:
            if not item.get("category"):
                item["category"] = default_category

    return ingest_items(
        db,
        items,
        source_type="file",
        source_name=file.filename,
        overwrite_existing=overwrite_existing,
    )


@router.get("/logs", response_model=List[dict])
def list_ingestion_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Return the most recent ingestion audit logs."""
    logs = crud.list_ingestion_logs(db, limit=limit)
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "source_type": log.source_type,
            "source_name": log.source_name,
            "total": log.total,
            "created": log.created_count,
            "updated": log.updated_count,
            "skipped": log.skipped_count,
            "errors": log.error_count,
            "error_messages": json.loads(log.errors) if log.errors else [],
            "duration_ms": log.duration_ms,
            "created_at": log.created_at.isoformat(),
        })
    return result
