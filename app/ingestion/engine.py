"""
Ingestion engine: takes a list of parsed items and upserts them into the DB.
Returns an IngestionResult and writes an IngestionLog row.
"""
from __future__ import annotations

import time
from typing import List, Optional

from sqlalchemy.orm import Session

from app import crud, schemas
from app.ingestion.parsers import ParsedItem


def ingest_items(
    db: Session,
    items: List[ParsedItem],
    source_type: str,
    source_name: Optional[str] = None,
    overwrite_existing: bool = False,
) -> schemas.IngestionResult:
    t0 = time.perf_counter()

    created = updated = skipped = errors = 0
    error_messages: List[str] = []

    for item in items:
        try:
            existing = crud.get_prompt_by_name(db, item["name"])
            if existing:
                if overwrite_existing:
                    update_data = schemas.PromptUpdate(
                        content=item["content"],
                        description=item.get("description") or existing.description,
                        category=item.get("category") or existing.category,
                        tags=item.get("tags") or [t.name for t in existing.tags],
                    )
                    crud.update_prompt(db, existing, update_data)
                    updated += 1
                else:
                    skipped += 1
            else:
                create_data = schemas.PromptCreate(
                    name=item["name"],
                    content=item["content"],
                    description=item.get("description") or None,
                    category=item.get("category") or None,
                    tags=item.get("tags") or [],
                )
                crud.create_prompt(
                    db,
                    create_data,
                    source=source_type,
                    source_file=source_name,
                )
                created += 1
        except Exception as exc:
            errors += 1
            error_messages.append(f"[{item.get('name', '?')}] {exc}")

    duration_ms = (time.perf_counter() - t0) * 1000

    crud.create_ingestion_log(
        db=db,
        source_type=source_type,
        source_name=source_name,
        total=len(items),
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors,
        error_messages=error_messages,
        duration_ms=duration_ms,
    )

    return schemas.IngestionResult(
        source_type=source_type,
        source_name=source_name,
        total=len(items),
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors,
        error_messages=error_messages,
        duration_ms=round(duration_ms, 2),
    )
