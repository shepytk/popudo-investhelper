"""Durable screening filters; no arbitrary SQL or user-provided owner IDs."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import Principal, current_user
from app.models import ScreeningPreset
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/me/screening-presets", tags=["my-screening-presets"])


class ScreeningFilters(BaseModel):
    q: str | None = Field(default=None, max_length=100)
    country_id: int | None = Field(default=None, ge=1)
    sector_id: int | None = Field(default=None, ge=1)


class NewPreset(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    filters: ScreeningFilters


class PresetOut(BaseModel):
    id: int
    name: str
    filters: ScreeningFilters


def _out(row: ScreeningPreset) -> PresetOut:
    return PresetOut(id=row.id, name=row.name, filters=ScreeningFilters.model_validate_json(row.filters_json))


def _owned(db: Session, preset_id: int, owner: Principal) -> ScreeningPreset:
    row = db.scalar(select(ScreeningPreset).where(
        ScreeningPreset.id == preset_id, ScreeningPreset.user_id == owner.user_id,
    ))
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "preset_not_found", "message": "Saved screen not found"})
    return row


@router.get("", response_model=list[PresetOut])
def list_presets(owner: Principal = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(ScreeningPreset).where(
        ScreeningPreset.user_id == owner.user_id,
    ).order_by(ScreeningPreset.id).limit(100)).all()
    return [_out(row) for row in rows]


@router.post("", response_model=PresetOut, status_code=201)
def create_preset(body: NewPreset, owner: Principal = Depends(current_user), db: Session = Depends(get_db)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail={"code": "invalid_name"})
    row = ScreeningPreset(
        name=name, user_id=owner.user_id,
        filters_json=body.filters.model_dump_json(exclude_none=True),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": "duplicate_preset", "message": "A screen with that name already exists"})
    db.refresh(row)
    return _out(row)


@router.get("/{preset_id}", response_model=PresetOut)
def get_preset(preset_id: int, owner: Principal = Depends(current_user), db: Session = Depends(get_db)):
    return _out(_owned(db, preset_id, owner))


@router.put("/{preset_id}", response_model=PresetOut)
def replace_preset(preset_id: int, body: NewPreset, owner: Principal = Depends(current_user), db: Session = Depends(get_db)):
    row = _owned(db, preset_id, owner)
    row.name = body.name.strip()
    if not row.name:
        raise HTTPException(status_code=422, detail={"code": "invalid_name"})
    row.filters_json = body.filters.model_dump_json(exclude_none=True)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": "duplicate_preset", "message": "A screen with that name already exists"})
    db.refresh(row)
    return _out(row)


@router.delete("/{preset_id}", status_code=204)
def delete_preset(preset_id: int, owner: Principal = Depends(current_user), db: Session = Depends(get_db)):
    row = _owned(db, preset_id, owner)
    db.delete(row)
    db.commit()
