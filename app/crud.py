"""
CRUD helpers for Prompt, Tag, PromptVersion, and IngestionLog.
All functions are synchronous and accept a SQLAlchemy Session.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app import models, schemas


# ─── Tag helpers ─────────────────────────────────────────────────────────────

def get_or_create_tag(db: Session, name: str) -> models.Tag:
    name = name.strip().lower()
    tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if not tag:
        tag = models.Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


def get_tags(db: Session) -> List[models.Tag]:
    return db.query(models.Tag).order_by(models.Tag.name).all()


# ─── Prompt helpers ───────────────────────────────────────────────────────────

def _estimate_tokens(text: str) -> int:
    """Very rough token estimator: ~4 chars per token."""
    return max(1, len(text) // 4)


def _resolve_tags(db: Session, tag_names: List[str]) -> List[models.Tag]:
    return [get_or_create_tag(db, n) for n in tag_names]


def create_prompt(
    db: Session,
    data: schemas.PromptCreate,
    source: str = "api",
    source_file: Optional[str] = None,
) -> models.Prompt:
    tags = _resolve_tags(db, data.tags or [])
    prompt = models.Prompt(
        name=data.name,
        content=data.content,
        description=data.description,
        category=data.category,
        source=source,
        source_file=source_file,
        version=1,
        token_count=_estimate_tokens(data.content),
        tags=tags,
    )
    db.add(prompt)
    db.flush()
    # Save initial version snapshot
    _snapshot(db, prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


def get_prompt(db: Session, prompt_id: int) -> Optional[models.Prompt]:
    return db.query(models.Prompt).filter(models.Prompt.id == prompt_id).first()


def get_prompt_by_name(db: Session, name: str) -> Optional[models.Prompt]:
    return db.query(models.Prompt).filter(models.Prompt.name == name).first()


def list_prompts(
    db: Session,
    q: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    is_active: Optional[bool] = None,
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[List[models.Prompt], int]:
    query = db.query(models.Prompt)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                models.Prompt.name.ilike(like),
                models.Prompt.content.ilike(like),
                models.Prompt.description.ilike(like),
            )
        )
    if category:
        query = query.filter(models.Prompt.category.ilike(f"%{category}%"))
    if is_active is not None:
        query = query.filter(models.Prompt.is_active == is_active)
    if source:
        query = query.filter(models.Prompt.source == source)
    if tags:
        for tag_name in tags:
            query = query.filter(
                models.Prompt.tags.any(models.Tag.name == tag_name.lower())
            )

    total = query.count()
    items = (
        query.order_by(models.Prompt.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def update_prompt(
    db: Session,
    prompt: models.Prompt,
    data: schemas.PromptUpdate,
) -> models.Prompt:
    changed = False

    if data.name is not None and data.name != prompt.name:
        prompt.name = data.name
        changed = True
    if data.description is not None and data.description != prompt.description:
        prompt.description = data.description
        changed = True
    if data.category is not None:
        prompt.category = data.category
        changed = True
    if data.is_active is not None:
        prompt.is_active = data.is_active
        changed = True
    if data.tags is not None:
        prompt.tags = _resolve_tags(db, data.tags)
        changed = True

    content_changed = data.content is not None and data.content != prompt.content
    if content_changed:
        prompt.content = data.content
        prompt.version += 1
        prompt.token_count = _estimate_tokens(data.content)
        _snapshot(db, prompt)
        changed = True

    if changed:
        prompt.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(prompt)
    return prompt


def delete_prompt(db: Session, prompt: models.Prompt) -> None:
    db.delete(prompt)
    db.commit()


def get_prompt_versions(db: Session, prompt_id: int) -> List[models.PromptVersion]:
    return (
        db.query(models.PromptVersion)
        .filter(models.PromptVersion.prompt_id == prompt_id)
        .order_by(models.PromptVersion.version)
        .all()
    )


def _snapshot(db: Session, prompt: models.Prompt) -> models.PromptVersion:
    v = models.PromptVersion(
        prompt_id=prompt.id,
        version=prompt.version,
        content=prompt.content,
        description=prompt.description,
    )
    db.add(v)
    db.flush()
    return v


# ─── Ingestion log ────────────────────────────────────────────────────────────

def create_ingestion_log(
    db: Session,
    source_type: str,
    source_name: Optional[str],
    total: int,
    created: int,
    updated: int,
    skipped: int,
    errors: int,
    error_messages: List[str],
    duration_ms: float,
) -> models.IngestionLog:
    log = models.IngestionLog(
        source_type=source_type,
        source_name=source_name,
        total=total,
        created_count=created,
        updated_count=updated,
        skipped_count=skipped,
        error_count=errors,
        errors=json.dumps(error_messages),
        duration_ms=duration_ms,
    )
    db.add(log)
    db.commit()
    return log


def list_ingestion_logs(db: Session, limit: int = 50) -> List[models.IngestionLog]:
    return (
        db.query(models.IngestionLog)
        .order_by(models.IngestionLog.created_at.desc())
        .limit(limit)
        .all()
    )


# ─── Stats ────────────────────────────────────────────────────────────────────

def get_stats(db: Session) -> Dict[str, Any]:
    total = db.query(func.count(models.Prompt.id)).scalar()
    active = db.query(func.count(models.Prompt.id)).filter(models.Prompt.is_active == True).scalar()
    tag_count = db.query(func.count(models.Tag.id)).scalar()
    category_count = (
        db.query(models.Prompt.category)
        .filter(models.Prompt.category.isnot(None))
        .distinct()
        .count()
    )
    source_rows = (
        db.query(models.Prompt.source, func.count(models.Prompt.id))
        .group_by(models.Prompt.source)
        .all()
    )
    ingestion_runs = db.query(func.count(models.IngestionLog.id)).scalar()

    return {
        "total_prompts": total,
        "active_prompts": active,
        "total_tags": tag_count,
        "total_categories": category_count,
        "sources": {src or "unknown": cnt for src, cnt in source_rows},
        "ingestion_runs": ingestion_runs,
    }
