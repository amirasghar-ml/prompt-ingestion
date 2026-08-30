"""
Parsers: turn raw file bytes into a list of BulkPromptItem dicts.
Supports JSON, JSONL, CSV, and plain-text (.txt / .md).
"""
from __future__ import annotations

import csv
import io
import json
from typing import List, Dict, Any


ParsedItem = Dict[str, Any]


def _require(item: dict, key: str, idx: int) -> str:
    val = item.get(key, "").strip()
    if not val:
        raise ValueError(f"Row {idx}: missing required field '{key}'")
    return val


# ─── JSON ─────────────────────────────────────────────────────────────────────

def parse_json(raw: bytes) -> List[ParsedItem]:
    data = json.loads(raw.decode("utf-8"))
    if isinstance(data, dict):
        # Single object wrapped in a dict — check for a list key
        for key in ("prompts", "items", "data"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
        else:
            data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON file must contain an array of prompt objects.")
    result = []
    for idx, item in enumerate(data):
        result.append({
            "name": _require(item, "name", idx),
            "content": _require(item, "content", idx),
            "description": item.get("description") or "",
            "category": item.get("category") or "",
            "tags": item.get("tags") or [],
        })
    return result


# ─── JSONL ────────────────────────────────────────────────────────────────────

def parse_jsonl(raw: bytes) -> List[ParsedItem]:
    result = []
    for idx, line in enumerate(raw.decode("utf-8").splitlines()):
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        result.append({
            "name": _require(item, "name", idx),
            "content": _require(item, "content", idx),
            "description": item.get("description") or "",
            "category": item.get("category") or "",
            "tags": item.get("tags") or [],
        })
    return result


# ─── CSV ──────────────────────────────────────────────────────────────────────
# Expected columns: name, content, description (opt), category (opt), tags (opt, comma-sep)

def parse_csv(raw: bytes) -> List[ParsedItem]:
    text = raw.decode("utf-8-sig")  # strip BOM if present
    reader = csv.DictReader(io.StringIO(text))
    result = []
    for idx, row in enumerate(reader):
        name = (row.get("name") or "").strip()
        content = (row.get("content") or "").strip()
        if not name or not content:
            raise ValueError(f"Row {idx + 2}: missing 'name' or 'content' column")
        raw_tags = row.get("tags") or ""
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        result.append({
            "name": name,
            "content": content,
            "description": (row.get("description") or "").strip(),
            "category": (row.get("category") or "").strip(),
            "tags": tags,
        })
    return result


# ─── Plain text / Markdown ────────────────────────────────────────────────────
# Each file is treated as a single prompt; caller supplies the name.

def parse_text(raw: bytes, filename: str) -> List[ParsedItem]:
    content = raw.decode("utf-8").strip()
    if not content:
        raise ValueError("File is empty.")
    # Use filename (without extension) as the prompt name
    name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip()
    return [{
        "name": name or filename,
        "content": content,
        "description": "",
        "category": "",
        "tags": [],
    }]


# ─── Dispatcher ───────────────────────────────────────────────────────────────

def parse_file(raw: bytes, filename: str) -> List[ParsedItem]:
    lower = filename.lower()
    if lower.endswith(".jsonl"):
        return parse_jsonl(raw)
    if lower.endswith(".json"):
        return parse_json(raw)
    if lower.endswith(".csv"):
        return parse_csv(raw)
    if lower.endswith(".txt") or lower.endswith(".md"):
        return parse_text(raw, filename)
    raise ValueError(
        f"Unsupported file type: '{filename}'. "
        "Supported formats: .json, .jsonl, .csv, .txt, .md"
    )
