from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.post("/", response_model=schemas.PromptOut, status_code=status.HTTP_201_CREATED)
def create_prompt(data: schemas.PromptCreate, db: Session = Depends(get_db)):
    existing = crud.get_prompt_by_name(db, data.name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Prompt with name '{data.name}' already exists. Use PUT to update.",
        )
    return crud.create_prompt(db, data, source="api")


@router.get("/", response_model=schemas.PaginatedPrompts)
def list_prompts(
    q: Optional[str] = Query(None, description="Search in name, content, description"),
    category: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    is_active: Optional[bool] = Query(None),
    source: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    items, total = crud.list_prompts(
        db, q=q, category=category, tags=tags,
        is_active=is_active, source=source,
        skip=skip, limit=limit,
    )
    return schemas.PaginatedPrompts(total=total, skip=skip, limit=limit, items=items)


@router.get("/stats", response_model=schemas.StatsOut)
def get_stats(db: Session = Depends(get_db)):
    return crud.get_stats(db)


@router.get("/tags", response_model=List[schemas.TagOut])
def list_tags(db: Session = Depends(get_db)):
    return crud.get_tags(db)


@router.get("/{prompt_id}", response_model=schemas.PromptOut)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = crud.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.put("/{prompt_id}", response_model=schemas.PromptOut)
def update_prompt(
    prompt_id: int,
    data: schemas.PromptUpdate,
    db: Session = Depends(get_db),
):
    prompt = crud.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return crud.update_prompt(db, prompt, data)


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = crud.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    crud.delete_prompt(db, prompt)


@router.get("/{prompt_id}/versions", response_model=List[schemas.PromptVersionOut])
def get_versions(prompt_id: int, db: Session = Depends(get_db)):
    prompt = crud.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return crud.get_prompt_versions(db, prompt_id)
