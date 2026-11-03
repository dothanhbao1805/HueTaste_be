import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.nguyen_lieu import NguyenLieu


def get_or_create(db: Session, ten: str, nhom: str | None = None) -> NguyenLieu:
    ten = ten.strip()
    nl = db.scalar(select(NguyenLieu).where(func.lower(NguyenLieu.tenNguyenLieu) == ten.lower()))
    if nl is None:
        nl = NguyenLieu(tenNguyenLieu=ten, nhomNguyenLieu=nhom)
        db.add(nl)
        db.flush()
    elif nhom and not nl.nhomNguyenLieu:
        nl.nhomNguyenLieu = nhom
    return nl


def search(db: Session, q: str | None, limit: int) -> list[NguyenLieu]:
    stmt = select(NguyenLieu)
    if q and q.strip():
        stmt = stmt.where(func.lower(NguyenLieu.tenNguyenLieu).like(f"%{q.strip().lower()}%"))
    return list(db.scalars(stmt.order_by(NguyenLieu.tenNguyenLieu).limit(limit)).all())


def get_many(db: Session, ids: list[uuid.UUID]) -> list[NguyenLieu]:
    if not ids:
        return []
    return list(db.scalars(select(NguyenLieu).where(NguyenLieu.idNguyenLieu.in_(ids))).all())
