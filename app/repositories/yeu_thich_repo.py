import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import TrangThaiNoiDung
from app.models.danh_sach_yeu_thich import DanhSachYeuThich
from app.models.dia_diem import DiaDiem
from app.models.mon_an import MonAn

_ACTIVE = TrangThaiNoiDung.ACTIVE.value


def get(
    db: Session, id_nguoi_dung: uuid.UUID, *, id_mon: uuid.UUID | None = None, id_dia_diem: uuid.UUID | None = None
) -> DanhSachYeuThich | None:
    """Đúng 1 trong id_mon / id_dia_diem."""
    cot = DanhSachYeuThich.idMonAn == id_mon if id_mon else DanhSachYeuThich.idDiaDiem == id_dia_diem
    return db.scalar(select(DanhSachYeuThich).where(DanhSachYeuThich.idNguoiDung == id_nguoi_dung, cot))


def create(db: Session, **fields) -> DanhSachYeuThich:
    yt = DanhSachYeuThich(**fields)
    db.add(yt)
    db.flush()
    return yt


def delete(db: Session, yt: DanhSachYeuThich) -> None:
    db.delete(yt)
    db.flush()


def list_mon(db: Session, id_nguoi_dung: uuid.UUID) -> list[MonAn]:
    stmt = (
        select(MonAn)
        .join(DanhSachYeuThich, DanhSachYeuThich.idMonAn == MonAn.idMonAn)
        .where(DanhSachYeuThich.idNguoiDung == id_nguoi_dung, MonAn.trangThai == _ACTIVE)
        .order_by(DanhSachYeuThich.ngayTao.desc())
    )
    return list(db.scalars(stmt).all())


def list_quan(db: Session, id_nguoi_dung: uuid.UUID) -> list[DiaDiem]:
    stmt = (
        select(DiaDiem)
        .join(DanhSachYeuThich, DanhSachYeuThich.idDiaDiem == DiaDiem.idDiaDiem)
        .where(DanhSachYeuThich.idNguoiDung == id_nguoi_dung, DiaDiem.trangThai == _ACTIVE)
        .order_by(DanhSachYeuThich.ngayTao.desc())
    )
    return list(db.scalars(stmt).all())
