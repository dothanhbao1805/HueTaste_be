import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import KetQuaChiTietBaoCao, TrangThaiBaoCao
from app.models.bao_cao import BaoCao
from app.models.chi_tiet_bao_cao import ChiTietBaoCao
from app.models.mon_an import MonAn


def create(db: Session, **fields) -> BaoCao:
    bc = BaoCao(**fields)
    db.add(bc)
    db.flush()
    return bc


def add_chi_tiet(db: Session, id_bao_cao: uuid.UUID, ids_mon: list[uuid.UUID]) -> None:
    db.add_all(
        ChiTietBaoCao(idBaoCao=id_bao_cao, idMonAn=m, ketQuaXuLy=KetQuaChiTietBaoCao.CHO_XU_LY.value)
        for m in ids_mon
    )
    db.flush()


def get_by_id(db: Session, id_bao_cao: uuid.UUID) -> BaoCao | None:
    return db.get(BaoCao, id_bao_cao)


def co_bao_cao_dang_cho(db: Session, id_nguoi_dung: uuid.UUID, id_dia_diem: uuid.UUID) -> bool:
    return (
        db.scalar(
            select(BaoCao.idBaoCao).where(
                BaoCao.idNguoiDung == id_nguoi_dung,
                BaoCao.idDiaDiem == id_dia_diem,
                BaoCao.trangThai == TrangThaiBaoCao.CHO_XU_LY.value,
            )
        )
        is not None
    )


def search(
    db: Session,
    *,
    id_nguoi_dung: uuid.UUID | None = None,
    trang_thai: str | None = None,
    page: int,
    size: int,
) -> tuple[list[BaoCao], int]:
    dieu_kien = []
    if id_nguoi_dung:
        dieu_kien.append(BaoCao.idNguoiDung == id_nguoi_dung)
    if trang_thai:
        dieu_kien.append(BaoCao.trangThai == trang_thai)
    total = db.scalar(select(func.count()).select_from(BaoCao).where(*dieu_kien)) or 0
    stmt = (
        select(BaoCao)
        .where(*dieu_kien)
        .order_by(BaoCao.ngayTao.desc(), BaoCao.idBaoCao)
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).all()), total


def chi_tiet_of(db: Session, ids_bao_cao: list[uuid.UUID]) -> dict[uuid.UUID, list[tuple[ChiTietBaoCao, MonAn]]]:
    if not ids_bao_cao:
        return {}
    stmt = (
        select(ChiTietBaoCao, MonAn)
        .join(MonAn, MonAn.idMonAn == ChiTietBaoCao.idMonAn)
        .where(ChiTietBaoCao.idBaoCao.in_(ids_bao_cao))
        .order_by(MonAn.tenMon)
    )
    ket_qua: dict[uuid.UUID, list[tuple[ChiTietBaoCao, MonAn]]] = {}
    for ct, mon in db.execute(stmt).all():
        ket_qua.setdefault(ct.idBaoCao, []).append((ct, mon))
    return ket_qua


def mon_bi_go(db: Session, id_mon: uuid.UUID, id_dia_diem: uuid.UUID) -> bool:
    """Admin đã xác nhận món này ở quán này là VI_PHAM -> pipeline không gắn lại."""
    stmt = (
        select(ChiTietBaoCao.idChiTietBaoCao)
        .join(BaoCao, BaoCao.idBaoCao == ChiTietBaoCao.idBaoCao)
        .where(
            BaoCao.idDiaDiem == id_dia_diem,
            ChiTietBaoCao.idMonAn == id_mon,
            ChiTietBaoCao.ketQuaXuLy == KetQuaChiTietBaoCao.VI_PHAM.value,
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None


def dem_cho_xu_ly(db: Session) -> int:
    stmt = select(func.count()).select_from(BaoCao).where(BaoCao.trangThai == TrangThaiBaoCao.CHO_XU_LY.value)
    return db.scalar(stmt) or 0
