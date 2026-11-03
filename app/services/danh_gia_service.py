"""Đánh giá món ăn / địa điểm. Điểm quán gộp rating Google (pipeline) với đánh giá trong app."""
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.constants import TrangThaiNoiDung
from app.core.exceptions import NotFoundError
from app.models.danh_gia import DanhGia
from app.models.dia_diem import DiaDiem
from app.models.nguoi_dung import NguoiDung
from app.repositories import danh_gia_repo
from app.schemas.danh_gia import DanhGiaOut, NguoiVietOut, TrangDanhGiaOut, VietDanhGia
from app.services import dia_diem_service, mon_an_service

NGUON_APP = "app"


def tinh_lai_diem_quan(db: Session, dd: DiaDiem) -> None:
    """diemTrungBinh = TB có trọng số của rating Google (soDanhGiaGoogle lượt) và các đánh giá app. Không commit."""
    tong_app, so_app = danh_gia_repo.thong_ke(db, id_dia_diem=dd.idDiaDiem)
    tong, so = float(tong_app), so_app
    if dd.diemGoogle is not None:
        so_google = dd.soDanhGiaGoogle or 1  # Serper không trả số lượt thì tính như 1 đánh giá
        tong += float(dd.diemGoogle) * so_google
        so += so_google
    dd.diemTrungBinh = Decimal(str(round(tong / so, 2))) if so else None


def _out(dg: DanhGia, nguoi: NguoiDung) -> DanhGiaOut:
    return DanhGiaOut(
        idDanhGia=dg.idDanhGia,
        idMonAn=dg.idMonAn,
        idDiaDiem=dg.idDiaDiem,
        diemSo=dg.diemSo,
        noiDung=dg.noiDung,
        ngayTao=dg.ngayTao,
        nguoiDung=NguoiVietOut.model_validate(nguoi),
    )


def viet(db: Session, user: NguoiDung, body: VietDanhGia) -> DanhGiaOut:
    """Mỗi người 1 đánh giá cho mỗi món/quán: viết lại thì cập nhật bản cũ."""
    dd = dia_diem_service.get_active(db, body.idDiaDiem) if body.idDiaDiem else None
    if body.idMonAn:
        mon_an_service.get_active(db, body.idMonAn)
    dg = danh_gia_repo.get_cua_nguoi_dung(db, user.idNguoiDung, id_mon=body.idMonAn, id_dia_diem=body.idDiaDiem)
    if dg is None:
        dg = danh_gia_repo.create(
            db,
            idNguoiDung=user.idNguoiDung,
            idMonAn=body.idMonAn,
            idDiaDiem=body.idDiaDiem,
            nguon=NGUON_APP,
            diemSo=body.diemSo,
            noiDung=body.noiDung,
            trangThai=TrangThaiNoiDung.ACTIVE.value,
        )
    else:
        dg.diemSo, dg.noiDung = body.diemSo, body.noiDung
        db.flush()
    if dd is not None:
        tinh_lai_diem_quan(db, dd)
    db.commit()
    db.refresh(dg)
    return _out(dg, user)


def xoa(db: Session, user: NguoiDung, id_danh_gia: uuid.UUID) -> None:
    dg = danh_gia_repo.get_by_id(db, id_danh_gia)
    if not dg or dg.idNguoiDung != user.idNguoiDung:
        raise NotFoundError("Không tìm thấy đánh giá", "DANH_GIA_NOT_FOUND")
    id_dia_diem = dg.idDiaDiem
    danh_gia_repo.delete(db, dg)
    if id_dia_diem:
        dd = db.get(DiaDiem, id_dia_diem)
        if dd is not None:
            tinh_lai_diem_quan(db, dd)
    db.commit()


def _trang(
    db: Session, so: int, diem_tb: float | None, *, id_mon=None, id_dia_diem=None, page: int, size: int
) -> TrangDanhGiaOut:
    rows = danh_gia_repo.list_theo_doi_tuong(db, id_mon=id_mon, id_dia_diem=id_dia_diem, page=page, size=size)
    return TrangDanhGiaOut(
        items=[_out(dg, nd) for dg, nd in rows], total=so, page=page, size=size, diemTrungBinh=diem_tb
    )


def list_mon(db: Session, id_mon: uuid.UUID, page: int, size: int) -> TrangDanhGiaOut:
    mon_an_service.get_active(db, id_mon)
    tong, so = danh_gia_repo.thong_ke(db, id_mon=id_mon)
    return _trang(db, so, round(tong / so, 2) if so else None, id_mon=id_mon, page=page, size=size)


def list_quan(db: Session, id_dia_diem: uuid.UUID, page: int, size: int) -> TrangDanhGiaOut:
    dd = dia_diem_service.get_active(db, id_dia_diem)
    _, so = danh_gia_repo.thong_ke(db, id_dia_diem=id_dia_diem)
    diem = float(dd.diemTrungBinh) if dd.diemTrungBinh is not None else None
    return _trang(db, so, diem, id_dia_diem=id_dia_diem, page=page, size=size)
