from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Table, Float
)
from sqlalchemy.orm import relationship
from app.database import Base

# Many-to-many: prompts <-> tags
prompt_tags = Table(
    "prompt_tags",
    Base.metadata,
    Column("prompt_id", Integer, ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    prompts = relationship("Prompt", secondary=prompt_tags, back_populates="tags")


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(128), nullable=True, index=True)
    source = Column(String(128), nullable=True)          # "api" | "file" | "bulk"
    source_file = Column(String(512), nullable=True)     # original filename if from file
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tags = relationship("Tag", secondary=prompt_tags, back_populates="prompts")
    versions = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan",
        order_by="PromptVersion.version",
    )


class PromptVersion(Base):
    """Immutable snapshot of a prompt at a given version number."""
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    prompt = relationship("Prompt", back_populates="versions")


class IngestionLog(Base):
    """Audit trail of every ingestion run."""
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(64), nullable=False)     # "api" | "file" | "bulk_json" | "bulk_csv"
    source_name = Column(String(512), nullable=True)
    total = Column(Integer, default=0)
    created_count = Column(Integer, default=0)
    updated_count = Column(Integer, default=0)
    skipped_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    errors = Column(Text, nullable=True)                 # JSON list of error messages
    duration_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
