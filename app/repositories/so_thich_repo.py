import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.so_thich import SoThich
from app.models.so_thich_nguoi_dung import SoThichNguoiDung


def get_or_create(db: Session, loai: str, ten: str) -> SoThich:
    ten = ten.strip()
    st = db.scalar(
        select(SoThich).where(SoThich.loai == loai, func.lower(SoThich.tenSoThich) == ten.lower())
    )
    if st is None:
        st = SoThich(loai=loai, tenSoThich=ten)
        db.add(st)
        db.flush()
    return st


def list_all(db: Session) -> list[SoThich]:
    return list(db.scalars(select(SoThich).order_by(SoThich.loai, SoThich.tenSoThich)).all())


def get_many(db: Session, ids: list[uuid.UUID]) -> list[SoThich]:
    if not ids:
        return []
    return list(db.scalars(select(SoThich).where(SoThich.idSoThich.in_(ids))).all())


def list_of_user(db: Session, id_nguoi_dung: uuid.UUID) -> list[tuple[SoThichNguoiDung, SoThich]]:
    stmt = (
        select(SoThichNguoiDung, SoThich)
        .join(SoThich, SoThich.idSoThich == SoThichNguoiDung.idSoThich)
        .where(SoThichNguoiDung.idNguoiDung == id_nguoi_dung)
        .order_by(SoThich.loai, SoThich.tenSoThich)
    )
    return [(r[0], r[1]) for r in db.execute(stmt).all()]


def replace_of_user(db: Session, id_nguoi_dung: uuid.UUID, items: list[tuple[uuid.UUID, int]]) -> None:
    db.execute(delete(SoThichNguoiDung).where(SoThichNguoiDung.idNguoiDung == id_nguoi_dung))
    for id_so_thich, muc_do in items:
        db.add(SoThichNguoiDung(idNguoiDung=id_nguoi_dung, idSoThich=id_so_thich, mucDo=muc_do))
    db.flush()
