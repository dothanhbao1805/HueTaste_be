import uuid
from collections import defaultdict

from sqlalchemy import delete, exists, func, select
from sqlalchemy.orm import Session

from app.core.chuan_hoa import chuan_hoa_ten
from app.core.constants import TrangThaiNoiDung
from app.models.danh_gia import DanhGia
from app.models.danh_sach_yeu_thich import DanhSachYeuThich
from app.models.dia_diem import DiaDiem
from app.models.mon_an import MonAn
from app.models.mon_an_che_do_an import MonAnCheDoAn
from app.models.mon_an_dia_diem import MonAnDiaDiem
from app.models.mon_an_nguyen_lieu import MonAnNguyenLieu
from app.models.mon_an_so_thich import MonAnSoThich
from app.models.nguyen_lieu import NguyenLieu
from app.models.so_thich import SoThich

_ACTIVE = TrangThaiNoiDung.ACTIVE.value


def get_by_id(db: Session, id_mon: uuid.UUID) -> MonAn | None:
    return db.get(MonAn, id_mon)


def get_by_wiki(db: Session, page_id: int) -> MonAn | None:
    return db.scalar(select(MonAn).where(MonAn.maWikipedia == page_id))


def get_by_ten_chuan_hoa(db: Session, keys: list[str]) -> MonAn | None:
    if not keys:
        return None
    return db.scalar(select(MonAn).where(MonAn.tenChuanHoa.in_(keys)).limit(1))


def list_ten(db: Session) -> list[str]:
    return list(db.scalars(select(MonAn.tenMon).order_by(MonAn.tenMon)).all())


def list_ten_chuan_hoa(db: Session) -> set[str]:
    return set(db.scalars(select(MonAn.tenChuanHoa)).all())


def create(db: Session, **fields) -> MonAn:
    mon = MonAn(**fields)
    db.add(mon)
    db.flush()
    return mon


def replace_nguyen_lieu(db: Session, id_mon: uuid.UUID, items: list[tuple[uuid.UUID, bool]]) -> None:
    db.execute(delete(MonAnNguyenLieu).where(MonAnNguyenLieu.idMonAn == id_mon))
    for id_nl, chinh in dict(items).items():  # dict: bỏ nguyên liệu lặp
        db.add(MonAnNguyenLieu(idMonAn=id_mon, idNguyenLieu=id_nl, laThanhPhanChinh=chinh))
    db.flush()


def replace_so_thich(db: Session, id_mon: uuid.UUID, items: list[tuple[uuid.UUID, float]]) -> None:
    db.execute(delete(MonAnSoThich).where(MonAnSoThich.idMonAn == id_mon))
    for id_st, trong_so in dict(items).items():
        db.add(MonAnSoThich(idMonAn=id_mon, idSoThich=id_st, trongSo=trong_so))
    db.flush()


def replace_che_do_an(db: Session, id_mon: uuid.UUID, ids: list[uuid.UUID]) -> None:
    db.execute(delete(MonAnCheDoAn).where(MonAnCheDoAn.idMonAn == id_mon))
    for id_cd in set(ids):
        db.add(MonAnCheDoAn(idMonAn=id_mon, idCheDoAn=id_cd))
    db.flush()


def list_active(db: Session) -> list[MonAn]:
    return list(db.scalars(select(MonAn).where(MonAn.trangThai == _ACTIVE).order_by(MonAn.tenMon)).all())


def list_chua_an(db: Session) -> list[MonAn]:
    """Món active + unverified (bỏ món admin ẩn): danh sách ứng viên cho scan ảnh."""
    return list(
        db.scalars(select(MonAn).where(MonAn.trangThai != TrangThaiNoiDung.HIDDEN.value).order_by(MonAn.tenMon)).all()
    )


def search(
    db: Session,
    *,
    q: str | None,
    id_danh_muc: uuid.UUID | None,
    nguyen_lieu: str | None,
    page: int,
    size: int,
) -> tuple[list[MonAn], int]:
    stmt = select(MonAn).where(MonAn.trangThai == _ACTIVE)
    if q:
        # so trên tenChuanHoa nên gõ không dấu vẫn tìm được
        stmt = stmt.where(MonAn.tenChuanHoa.like(f"%{chuan_hoa_ten(q)}%"))
    if id_danh_muc:
        stmt = stmt.where(MonAn.idDanhMucMonAn == id_danh_muc)
    if nguyen_lieu:
        stmt = stmt.where(
            exists(
                select(MonAnNguyenLieu.idMonAnNguyenLieu)
                .join(NguyenLieu, NguyenLieu.idNguyenLieu == MonAnNguyenLieu.idNguyenLieu)
                .where(
                    MonAnNguyenLieu.idMonAn == MonAn.idMonAn,
                    func.lower(NguyenLieu.tenNguyenLieu).like(f"%{nguyen_lieu.strip().lower()}%"),
                )
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(MonAn.tenMon).offset((page - 1) * size).limit(size)).all()
    return list(items), total


def nguyen_lieu_of(db: Session, id_mon: uuid.UUID) -> list[tuple[NguyenLieu, bool]]:
    stmt = (
        select(NguyenLieu, MonAnNguyenLieu.laThanhPhanChinh)
        .join(MonAnNguyenLieu, MonAnNguyenLieu.idNguyenLieu == NguyenLieu.idNguyenLieu)
        .where(MonAnNguyenLieu.idMonAn == id_mon)
        .order_by(MonAnNguyenLieu.laThanhPhanChinh.desc(), NguyenLieu.tenNguyenLieu)
    )
    return [(r[0], r[1]) for r in db.execute(stmt).all()]


def so_thich_of(db: Session, ids_mon: list[uuid.UUID]) -> dict[uuid.UUID, list[tuple[SoThich, float]]]:
    out: dict[uuid.UUID, list[tuple[SoThich, float]]] = defaultdict(list)
    if not ids_mon:
        return out
    stmt = (
        select(MonAnSoThich.idMonAn, SoThich, MonAnSoThich.trongSo)
        .join(SoThich, SoThich.idSoThich == MonAnSoThich.idSoThich)
        .where(MonAnSoThich.idMonAn.in_(ids_mon))
    )
    for id_mon, st, trong_so in db.execute(stmt).all():
        out[id_mon].append((st, float(trong_so)))
    return out


def mon_chua_nguyen_lieu(db: Session, ids_nguyen_lieu: list[uuid.UUID]) -> set[uuid.UUID]:
    if not ids_nguyen_lieu:
        return set()
    stmt = select(MonAnNguyenLieu.idMonAn).where(MonAnNguyenLieu.idNguyenLieu.in_(ids_nguyen_lieu)).distinct()
    return set(db.scalars(stmt).all())


def che_do_an_of(db: Session, ids_mon: list[uuid.UUID]) -> dict[uuid.UUID, set[uuid.UUID]]:
    out: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
    if not ids_mon:
        return out
    stmt = select(MonAnCheDoAn.idMonAn, MonAnCheDoAn.idCheDoAn).where(MonAnCheDoAn.idMonAn.in_(ids_mon))
    for id_mon, id_cd in db.execute(stmt).all():
        out[id_mon].add(id_cd)
    return out


def diem_danh_gia_tb(db: Session, ids_mon: list[uuid.UUID]) -> dict[uuid.UUID, float]:
    if not ids_mon:
        return {}
    stmt = (
        select(DanhGia.idMonAn, func.avg(DanhGia.diemSo))
        .where(DanhGia.idMonAn.in_(ids_mon), DanhGia.trangThai == TrangThaiNoiDung.ACTIVE.value)
        .group_by(DanhGia.idMonAn)
    )
    return {r[0]: float(r[1]) for r in db.execute(stmt).all()}


def rating_quan_tb(db: Session, ids_mon: list[uuid.UUID]) -> dict[uuid.UUID, float]:
    """Rating Google trung bình của các quán bán món - thay cho đánh giá khi app chưa có review."""
    if not ids_mon:
        return {}
    stmt = (
        select(MonAnDiaDiem.idMonAn, func.avg(DiaDiem.diemTrungBinh))
        .join(DiaDiem, DiaDiem.idDiaDiem == MonAnDiaDiem.idDiaDiem)
        .where(MonAnDiaDiem.idMonAn.in_(ids_mon), DiaDiem.diemTrungBinh.is_not(None))
        .group_by(MonAnDiaDiem.idMonAn)
    )
    return {r[0]: float(r[1]) for r in db.execute(stmt).all()}


def yeu_thich_ids(db: Session, id_nguoi_dung: uuid.UUID) -> set[uuid.UUID]:
    stmt = select(DanhSachYeuThich.idMonAn).where(
        DanhSachYeuThich.idNguoiDung == id_nguoi_dung, DanhSachYeuThich.idMonAn.is_not(None)
    )
    return set(db.scalars(stmt).all())
