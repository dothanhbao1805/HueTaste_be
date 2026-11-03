import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import TrangThaiNoiDung
from app.models.danh_gia import DanhGia
from app.models.nguoi_dung import NguoiDung

_ACTIVE = TrangThaiNoiDung.ACTIVE.value


def _doi_tuong(id_mon: uuid.UUID | None, id_dia_diem: uuid.UUID | None):
    return DanhGia.idMonAn == id_mon if id_mon else DanhGia.idDiaDiem == id_dia_diem


def get_by_id(db: Session, id_danh_gia: uuid.UUID) -> DanhGia | None:
    return db.get(DanhGia, id_danh_gia)


def get_cua_nguoi_dung(
    db: Session, id_nguoi_dung: uuid.UUID, *, id_mon: uuid.UUID | None = None, id_dia_diem: uuid.UUID | None = None
) -> DanhGia | None:
    return db.scalar(
        select(DanhGia).where(DanhGia.idNguoiDung == id_nguoi_dung, _doi_tuong(id_mon, id_dia_diem))
    )


def create(db: Session, **fields) -> DanhGia:
    dg = DanhGia(**fields)
    db.add(dg)
    db.flush()
    return dg


def delete(db: Session, dg: DanhGia) -> None:
    db.delete(dg)
    db.flush()


def list_theo_doi_tuong(
    db: Session, *, id_mon: uuid.UUID | None = None, id_dia_diem: uuid.UUID | None = None, page: int, size: int
) -> list[tuple[DanhGia, NguoiDung]]:
    stmt = (
        select(DanhGia, NguoiDung)
        .join(NguoiDung, NguoiDung.idNguoiDung == DanhGia.idNguoiDung)
        .where(_doi_tuong(id_mon, id_dia_diem), DanhGia.trangThai == _ACTIVE)
        .order_by(DanhGia.ngayTao.desc(), DanhGia.idDanhGia)
        .offset((page - 1) * size)
        .limit(size)
    )
    return [(r[0], r[1]) for r in db.execute(stmt).all()]


def thong_ke(
    db: Session, *, id_mon: uuid.UUID | None = None, id_dia_diem: uuid.UUID | None = None
) -> tuple[int, int]:
    """(tổng điểm, số đánh giá active)."""
    tong, so = db.execute(
        select(func.coalesce(func.sum(DanhGia.diemSo), 0), func.count()).where(
            _doi_tuong(id_mon, id_dia_diem), DanhGia.trangThai == _ACTIVE
        )
    ).one()
    return int(tong), int(so)
