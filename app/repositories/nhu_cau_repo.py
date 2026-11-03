import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.nhu_cau_theo_ngay import NhuCauTheoNgay


def ghep_ids(ids: list[uuid.UUID] | None) -> str | None:
    """list idNguyenLieu -> CSV lưu ở cột nguyenLieuTranh."""
    return ",".join(str(i) for i in ids) if ids else None


def tach_ids(csv: str | None) -> list[uuid.UUID]:
    return [uuid.UUID(x) for x in (csv or "").split(",") if x]


def get(db: Session, id_nguoi_dung: uuid.UUID, ngay: date, bua_an: str) -> NhuCauTheoNgay | None:
    return db.scalar(
        select(NhuCauTheoNgay).where(
            NhuCauTheoNgay.idNguoiDung == id_nguoi_dung,
            NhuCauTheoNgay.ngay == ngay,
            NhuCauTheoNgay.buaAn == bua_an,
        )
    )


def get_by_id(db: Session, id_nhu_cau: uuid.UUID) -> NhuCauTheoNgay | None:
    return db.get(NhuCauTheoNgay, id_nhu_cau)


def upsert(db: Session, id_nguoi_dung: uuid.UUID, ngay: date, bua_an: str, **truong: Any) -> NhuCauTheoNgay:
    """Mỗi người dùng có 1 bản ghi cho mỗi (ngày, bữa). Chỉ ghi các cột được truyền trong `truong`."""
    nc = get(db, id_nguoi_dung, ngay, bua_an)
    if nc is None:
        nc = NhuCauTheoNgay(idNguoiDung=id_nguoi_dung, ngay=ngay, buaAn=bua_an)
        db.add(nc)
    for cot, gia_tri in truong.items():
        setattr(nc, cot, gia_tri)
    db.flush()
    return nc


def list_theo_ngay(db: Session, id_nguoi_dung: uuid.UUID, ngay: date) -> list[NhuCauTheoNgay]:
    stmt = select(NhuCauTheoNgay).where(
        NhuCauTheoNgay.idNguoiDung == id_nguoi_dung, NhuCauTheoNgay.ngay == ngay
    )
    return list(db.scalars(stmt).all())


def delete(db: Session, nc: NhuCauTheoNgay) -> None:
    db.delete(nc)
    db.flush()
