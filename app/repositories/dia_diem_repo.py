import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import TrangThaiNoiDung
from app.models.dia_diem import DiaDiem
from app.models.mon_an import MonAn
from app.models.mon_an_dia_diem import MonAnDiaDiem

_ACTIVE = TrangThaiNoiDung.ACTIVE.value


def get_by_id(db: Session, id_dia_diem: uuid.UUID) -> DiaDiem | None:
    return db.get(DiaDiem, id_dia_diem)


def get_by_place_id(db: Session, place_id: str) -> DiaDiem | None:
    return db.scalar(select(DiaDiem).where(DiaDiem.maGooglePlace == place_id))


def create(db: Session, **fields) -> DiaDiem:
    dd = DiaDiem(**fields)
    db.add(dd)
    db.flush()
    return dd


def link_mon(db: Session, id_mon: uuid.UUID, id_dia_diem: uuid.UUID, la_dac_trung: bool) -> MonAnDiaDiem:
    link = get_link(db, id_mon, id_dia_diem)
    if link is None:
        link = MonAnDiaDiem(idMonAn=id_mon, idDiaDiem=id_dia_diem, laMonDacTrung=la_dac_trung)
        db.add(link)
        db.flush()
    else:
        link.laMonDacTrung = link.laMonDacTrung or la_dac_trung
    return link


def search(
    db: Session,
    *,
    q: str | None,
    id_mon: uuid.UUID | None,
    bbox: tuple[float, float, float, float] | None,
    gioi_han: int,
) -> list[DiaDiem]:
    """Lọc thô trong SQL; khoảng cách chính xác và phân trang do service tính."""
    stmt = select(DiaDiem).where(DiaDiem.trangThai == _ACTIVE)
    if q:
        stmt = stmt.where(func.lower(DiaDiem.tenDiaDiem).like(f"%{q.strip().lower()}%"))
    if id_mon:
        stmt = stmt.where(
            DiaDiem.idDiaDiem.in_(select(MonAnDiaDiem.idDiaDiem).where(MonAnDiaDiem.idMonAn == id_mon))
        )
    if bbox:
        vi_min, vi_max, kinh_min, kinh_max = bbox
        stmt = stmt.where(
            DiaDiem.viDo.between(vi_min, vi_max), DiaDiem.kinhDo.between(kinh_min, kinh_max)
        )
    stmt = stmt.order_by(DiaDiem.diemTrungBinh.desc(), DiaDiem.tenDiaDiem).limit(gioi_han)
    return list(db.scalars(stmt).all())


def mon_of(db: Session, id_dia_diem: uuid.UUID) -> list[tuple[MonAnDiaDiem, MonAn]]:
    stmt = (
        select(MonAnDiaDiem, MonAn)
        .join(MonAn, MonAn.idMonAn == MonAnDiaDiem.idMonAn)
        .where(MonAnDiaDiem.idDiaDiem == id_dia_diem, MonAn.trangThai == _ACTIVE)
        .order_by(MonAnDiaDiem.laMonDacTrung.desc(), MonAn.tenMon)
    )
    return [(r[0], r[1]) for r in db.execute(stmt).all()]


def quan_of_mons(db: Session, ids_mon: list[uuid.UUID]) -> list[tuple[MonAnDiaDiem, DiaDiem]]:
    if not ids_mon:
        return []
    stmt = (
        select(MonAnDiaDiem, DiaDiem)
        .join(DiaDiem, DiaDiem.idDiaDiem == MonAnDiaDiem.idDiaDiem)
        .where(MonAnDiaDiem.idMonAn.in_(ids_mon), DiaDiem.trangThai == _ACTIVE)
    )
    return [(r[0], r[1]) for r in db.execute(stmt).all()]


def get_link(db: Session, id_mon: uuid.UUID, id_dia_diem: uuid.UUID) -> MonAnDiaDiem | None:
    return db.scalar(
        select(MonAnDiaDiem).where(MonAnDiaDiem.idMonAn == id_mon, MonAnDiaDiem.idDiaDiem == id_dia_diem)
    )


def unlink_mon(db: Session, id_mon: uuid.UUID, id_dia_diem: uuid.UUID) -> None:
    link = get_link(db, id_mon, id_dia_diem)
    if link is not None:
        db.delete(link)
        db.flush()
