import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.nguoi_dung import NguoiDung


def get_by_id(db: Session, user_id: uuid.UUID) -> NguoiDung | None:
    return db.get(NguoiDung, user_id)


def get_by_email(db: Session, email: str) -> NguoiDung | None:
    return db.scalar(select(NguoiDung).where(NguoiDung.email == email.lower()))


def create(db: Session, **fields) -> NguoiDung:
    user = NguoiDung(**fields)
    db.add(user)
    db.flush()
    return user


def search(
    db: Session,
    *,
    q: str | None,
    vai_tro: str | None,
    trang_thai: str | None,
    page: int,
    size: int,
) -> tuple[list[NguoiDung], int]:
    stmt = select(NguoiDung)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(NguoiDung.email).like(like), func.lower(NguoiDung.hoTen).like(like))
        )
    if vai_tro:
        stmt = stmt.where(NguoiDung.vaiTro == vai_tro)
    if trang_thai:
        stmt = stmt.where(NguoiDung.trangThai == trang_thai)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(NguoiDung.ngayTao.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return list(items), total
