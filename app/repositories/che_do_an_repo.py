import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.che_do_an import CheDoAn
from app.models.che_do_an_nguoi_dung import CheDoAnNguoiDung


def get_or_create(db: Session, ten: str) -> CheDoAn:
    ten = ten.strip()
    cd = db.scalar(select(CheDoAn).where(func.lower(CheDoAn.tenCheDo) == ten.lower()))
    if cd is None:
        cd = CheDoAn(tenCheDo=ten)
        db.add(cd)
        db.flush()
    return cd


def get_by_ten(db: Session, ten: str) -> CheDoAn | None:
    return db.scalar(select(CheDoAn).where(func.lower(CheDoAn.tenCheDo) == ten.strip().lower()))


def list_all(db: Session) -> list[CheDoAn]:
    return list(db.scalars(select(CheDoAn).order_by(CheDoAn.tenCheDo)).all())


def get_many(db: Session, ids: list[uuid.UUID]) -> list[CheDoAn]:
    if not ids:
        return []
    return list(db.scalars(select(CheDoAn).where(CheDoAn.idCheDoAn.in_(ids))).all())


def list_of_user(db: Session, id_nguoi_dung: uuid.UUID) -> list[tuple[CheDoAnNguoiDung, CheDoAn]]:
    stmt = (
        select(CheDoAnNguoiDung, CheDoAn)
        .join(CheDoAn, CheDoAn.idCheDoAn == CheDoAnNguoiDung.idCheDoAn)
        .where(CheDoAnNguoiDung.idNguoiDung == id_nguoi_dung)
        .order_by(CheDoAn.tenCheDo)
    )
    return [(r[0], r[1]) for r in db.execute(stmt).all()]


def replace_of_user(
    db: Session, id_nguoi_dung: uuid.UUID, items: list[tuple[uuid.UUID, str | None]]
) -> None:
    db.execute(delete(CheDoAnNguoiDung).where(CheDoAnNguoiDung.idNguoiDung == id_nguoi_dung))
    for id_che_do, ghi_chu in items:
        db.add(CheDoAnNguoiDung(idNguoiDung=id_nguoi_dung, idCheDoAn=id_che_do, ghiChu=ghi_chu))
    db.flush()
