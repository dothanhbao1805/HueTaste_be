from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import LoaiGoiY, TrangThaiNoiDung, VaiTro
from app.models.danh_gia import DanhGia
from app.models.dia_diem import DiaDiem
from app.models.goi_y import GoiY
from app.models.mon_an import MonAn
from app.models.ngu_canh import NguCanh
from app.models.nguoi_dung import NguoiDung

_ACTIVE = TrangThaiNoiDung.ACTIVE.value


def _dem(db: Session, model, *dieu_kien) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*dieu_kien)) or 0


def dem_nguoi_dung(db: Session, tu: datetime | None = None) -> int:
    dk = [NguoiDung.vaiTro == VaiTro.USER.value]
    if tu:
        dk.append(NguoiDung.ngayTao >= tu)
    return _dem(db, NguoiDung, *dk)


def dem_mon_hien_thi(db: Session) -> int:
    return _dem(db, MonAn, MonAn.trangThai == _ACTIVE)


def dem_quan_hien_thi(db: Session) -> int:
    return _dem(db, DiaDiem, DiaDiem.trangThai == _ACTIVE)


def dem_danh_gia(db: Session) -> int:
    return _dem(db, DanhGia, DanhGia.trangThai == _ACTIVE)


def luot_goi_y_theo_ngay(db: Session, tu: datetime) -> dict[date, int]:
    """Mỗi lần gọi /goi-y tạo đúng 1 NguCanh -> đếm NguCanh theo ngày."""
    ngay = func.date(NguCanh.thoiDiem)
    stmt = select(ngay, func.count()).where(NguCanh.thoiDiem >= tu).group_by(ngay)
    # SQLite trả chuỗi 'YYYY-MM-DD', MySQL trả date
    return {(d if isinstance(d, date) else date.fromisoformat(d)): n for d, n in db.execute(stmt).all()}


def top_mon_goi_y(db: Session, tu: datetime, gioi_han: int) -> list[tuple[MonAn, int]]:
    so_lan = func.count(GoiY.idGoiY)
    stmt = (
        select(MonAn, so_lan)
        .join(GoiY, GoiY.idMonAn == MonAn.idMonAn)
        .where(GoiY.loaiGoiY == LoaiGoiY.MON_AN.value, GoiY.ngayTao >= tu)
        .group_by(MonAn.idMonAn)
        .order_by(so_lan.desc(), MonAn.tenMon)
        .limit(gioi_han)
    )
    return [(r[0], r[1]) for r in db.execute(stmt).all()]
