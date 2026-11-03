import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.danh_muc_mon_an import DanhMucMonAn
from app.models.mon_an import MonAn


def get_or_create(db: Session, ten: str) -> DanhMucMonAn:
    ten = ten.strip()
    dm = get_by_ten(db, ten)
    if dm is None:
        dm = DanhMucMonAn(tenDanhMuc=ten)
        db.add(dm)
        db.flush()
    return dm


def get_by_id(db: Session, id_danh_muc: uuid.UUID) -> DanhMucMonAn | None:
    return db.get(DanhMucMonAn, id_danh_muc)


def list_all(db: Session) -> list[DanhMucMonAn]:
    return list(db.scalars(select(DanhMucMonAn).order_by(DanhMucMonAn.tenDanhMuc)).all())


def get_by_ten(db: Session, ten: str) -> DanhMucMonAn | None:
    # vài chục dòng: so trong Python để không phụ thuộc collation (SQLite lower() bỏ qua chữ có dấu)
    khoa = ten.strip().casefold()
    return next((dm for dm in list_all(db) if dm.tenDanhMuc.casefold() == khoa), None)


def create(db: Session, **fields) -> DanhMucMonAn:
    dm = DanhMucMonAn(**fields)
    db.add(dm)
    db.flush()
    return dm


def delete(db: Session, dm: DanhMucMonAn) -> None:
    db.delete(dm)
    db.flush()


def dem_mon(db: Session) -> dict[uuid.UUID, int]:
    """Số món (mọi trạng thái) theo từng danh mục."""
    stmt = select(MonAn.idDanhMucMonAn, func.count()).group_by(MonAn.idDanhMucMonAn)
    return {r[0]: r[1] for r in db.execute(stmt).all()}
