"""Ảnh phụ của món/quán. Chỉ flush, không commit."""
import hashlib
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.anh_dia_diem import AnhDiaDiem
from app.models.anh_mon_an import AnhMonAn


def hash_url(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _dem(db: Session, model: Any, cot: Any, id_cha: uuid.UUID) -> int:
    return db.scalar(select(func.count()).select_from(model).where(cot == id_cha)) or 0


def _list(db: Session, model: Any, cot: Any, id_cha: uuid.UUID) -> list[Any]:
    return list(db.scalars(select(model).where(cot == id_cha).order_by(model.thuTu, model.ngayTao)).all())


def _them(db: Session, model: Any, cot_cha: str, id_cha: uuid.UUID, anh: dict[str, Any]) -> bool:
    """Thêm 1 ảnh; False nếu URL đã có. anh: {url, thumbnail, nguon}."""
    url = anh["url"]
    h = hash_url(url)
    cot = getattr(model, cot_cha)
    if db.scalar(select(model.urlHash).where(cot == id_cha, model.urlHash == h)) is not None:
        return False
    thu_tu = _dem(db, model, cot, id_cha)
    db.add(
        model(
            **{cot_cha: id_cha},
            url=url,
            urlHash=h,
            urlThumbnail=anh.get("thumbnail"),
            nguon=(anh.get("nguon") or None) and anh["nguon"][:255],
            thuTu=thu_tu,
        )
    )
    db.flush()
    return True


def dem_mon(db: Session, id_mon: uuid.UUID) -> int:
    return _dem(db, AnhMonAn, AnhMonAn.idMonAn, id_mon)


def list_mon(db: Session, id_mon: uuid.UUID) -> list[AnhMonAn]:
    return _list(db, AnhMonAn, AnhMonAn.idMonAn, id_mon)


def them_mon(db: Session, id_mon: uuid.UUID, anh: dict[str, Any]) -> bool:
    return _them(db, AnhMonAn, "idMonAn", id_mon, anh)


def dem_dia_diem(db: Session, id_dia_diem: uuid.UUID) -> int:
    return _dem(db, AnhDiaDiem, AnhDiaDiem.idDiaDiem, id_dia_diem)


def list_dia_diem(db: Session, id_dia_diem: uuid.UUID) -> list[AnhDiaDiem]:
    return _list(db, AnhDiaDiem, AnhDiaDiem.idDiaDiem, id_dia_diem)


def them_dia_diem(db: Session, id_dia_diem: uuid.UUID, anh: dict[str, Any]) -> bool:
    return _them(db, AnhDiaDiem, "idDiaDiem", id_dia_diem, anh)
