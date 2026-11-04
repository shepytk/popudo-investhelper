"""Owner-scoped CRUD; never accept a client-supplied user ID."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Principal, current_user
from app.models import Company, Watchlist, WatchlistItem
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/me/watchlists", tags=["my-watchlists"])


class NewWatchlist(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WatchlistOut(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class NewItem(BaseModel):
    company_id: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=2000)


class WatchlistItemOut(BaseModel):
    id: int
    company_id: int
    notes: str | None
    model_config = ConfigDict(from_attributes=True)


def _owner_list(db: Session, watchlist_id: int, principal: Principal) -> Watchlist:
    watchlist = db.scalar(select(Watchlist).where(
        Watchlist.id == watchlist_id, Watchlist.user_id == principal.user_id,
    ))
    if watchlist is None:
        raise HTTPException(status_code=404, detail={"code": "watchlist_not_found", "message": "Watchlist not found"})
    return watchlist


@router.get("", response_model=list[WatchlistOut])
def list_watchlists(principal: Principal = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Watchlist).where(
        Watchlist.user_id == principal.user_id,
    ).order_by(Watchlist.id).limit(100)))


@router.post("", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
def create_watchlist(body: NewWatchlist, principal: Principal = Depends(current_user), db: Session = Depends(get_db)):
    watchlist = Watchlist(user_id=principal.user_id, name=body.name.strip())
    if not watchlist.name:
        raise HTTPException(status_code=422, detail={"code": "invalid_name", "message": "Name required"})
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)
    return watchlist


@router.get("/{watchlist_id}", response_model=WatchlistOut)
def get_watchlist(watchlist_id: int, principal: Principal = Depends(current_user), db: Session = Depends(get_db)):
    return _owner_list(db, watchlist_id, principal)


@router.patch("/{watchlist_id}", response_model=WatchlistOut)
def rename_watchlist(
    watchlist_id: int, body: NewWatchlist,
    principal: Principal = Depends(current_user), db: Session = Depends(get_db),
):
    watchlist = _owner_list(db, watchlist_id, principal)
    if not body.name.strip():
        raise HTTPException(status_code=422, detail={"code": "invalid_name", "message": "Name required"})
    watchlist.name = body.name.strip()
    db.commit()
    db.refresh(watchlist)
    return watchlist


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist(watchlist_id: int, principal: Principal = Depends(current_user), db: Session = Depends(get_db)):
    watchlist = _owner_list(db, watchlist_id, principal)
    db.query(WatchlistItem).filter(WatchlistItem.watchlist_id == watchlist.id).delete(synchronize_session=False)
    db.delete(watchlist)
    db.commit()


@router.get("/{watchlist_id}/items", response_model=list[WatchlistItemOut])
def list_items(watchlist_id: int, principal: Principal = Depends(current_user), db: Session = Depends(get_db)):
    _owner_list(db, watchlist_id, principal)
    return list(db.scalars(select(WatchlistItem).where(
        WatchlistItem.watchlist_id == watchlist_id,
    ).order_by(WatchlistItem.id).limit(1000)))


@router.post("/{watchlist_id}/items", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED)
def add_item(watchlist_id: int, body: NewItem, principal: Principal = Depends(current_user), db: Session = Depends(get_db)):
    _owner_list(db, watchlist_id, principal)
    if db.get(Company, body.company_id) is None:
        raise HTTPException(status_code=404, detail={"code": "company_not_found", "message": "Company not found"})
    exists = db.scalar(select(WatchlistItem).where(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.company_id == body.company_id,
    ))
    if exists:
        return exists
    item = WatchlistItem(watchlist_id=watchlist_id, company_id=body.company_id, notes=body.notes)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{watchlist_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(watchlist_id: int, item_id: int, principal: Principal = Depends(current_user), db: Session = Depends(get_db)):
    _owner_list(db, watchlist_id, principal)
    item = db.scalar(select(WatchlistItem).where(
        WatchlistItem.id == item_id,
        WatchlistItem.watchlist_id == watchlist_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail={"code": "item_not_found", "message": "Item not found"})
    db.delete(item)
    db.commit()
