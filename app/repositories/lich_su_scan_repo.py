import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lich_su_scan import LichSuScan


def create(db: Session, **fields) -> LichSuScan:
    scan = LichSuScan(**fields)
    db.add(scan)
    db.flush()
    return scan


def get_by_id(db: Session, id_scan: uuid.UUID) -> LichSuScan | None:
    return db.get(LichSuScan, id_scan)


def dem_tu(db: Session, id_nguoi_dung: uuid.UUID, tu: datetime) -> int:
    return db.scalar(
        select(func.count())
        .select_from(LichSuScan)
        .where(LichSuScan.idNguoiDung == id_nguoi_dung, LichSuScan.ngayTao >= tu)
    )


def list_cua_user(db: Session, id_nguoi_dung: uuid.UUID, page: int, size: int) -> tuple[list[LichSuScan], int]:
    dieu_kien = LichSuScan.idNguoiDung == id_nguoi_dung
    total = db.scalar(select(func.count()).select_from(LichSuScan).where(dieu_kien))
    items = db.scalars(
        select(LichSuScan)
        .where(dieu_kien)
        .order_by(LichSuScan.ngayTao.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return list(items), total


def list_khong_gan_mon(db: Session) -> list[LichSuScan]:
    """Các lượt scan không gắn món (món không đặc trưng Huế / không phải món ăn) – để admin thống kê."""
    return list(db.scalars(select(LichSuScan).where(LichSuScan.idMonAn.is_(None))).all())
