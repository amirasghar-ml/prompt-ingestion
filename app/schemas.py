from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


# ─── Tag ────────────────────────────────────────────────────────────────────

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="Tag name")


class TagCreate(TagBase):
    pass


class TagOut(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Prompt ─────────────────────────────────────────────────────────────────

class PromptBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=128)
    tags: Optional[List[str]] = Field(default_factory=list)

    @validator("tags", pre=True, always=True)
    def coerce_tags(cls, v):
        if v is None:
            return []
        return [t.strip().lower() for t in v if t.strip()]


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=128)
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

    @validator("tags", pre=True, always=True)
    def coerce_tags(cls, v):
        if v is None:
            return None
        return [t.strip().lower() for t in v if t.strip()]


class PromptVersionOut(BaseModel):
    id: int
    version: int
    content: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PromptOut(BaseModel):
    id: int
    name: str
    content: str
    description: Optional[str]
    category: Optional[str]
    source: Optional[str]
    source_file: Optional[str]
    version: int
    is_active: bool
    token_count: Optional[int]
    tags: List[TagOut]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptListOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    source: Optional[str]
    version: int
    is_active: bool
    token_count: Optional[int]
    tags: List[TagOut]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Ingestion ───────────────────────────────────────────────────────────────

class BulkPromptItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)


class BulkIngestRequest(BaseModel):
    prompts: List[BulkPromptItem] = Field(..., min_items=1)
    overwrite_existing: bool = Field(
        False,
        description="If True, existing prompts with the same name are updated; otherwise skipped.",
    )


class IngestionResult(BaseModel):
    source_type: str
    source_name: Optional[str]
    total: int
    created: int
    updated: int
    skipped: int
    errors: int
    error_messages: List[str]
    duration_ms: float


# ─── Search ──────────────────────────────────────────────────────────────────

class SearchParams(BaseModel):
    q: Optional[str] = Field(None, description="Full-text search in name/content/description")
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    source: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=200)


class PaginatedPrompts(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[PromptListOut]


# ─── Stats ───────────────────────────────────────────────────────────────────

class StatsOut(BaseModel):
    total_prompts: int
    active_prompts: int
    total_tags: int
    total_categories: int
    sources: dict
    ingestion_runs: int
