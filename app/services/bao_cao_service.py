"""Người dùng báo cáo quán (kèm món sai), admin duyệt: món VI_PHAM bị gỡ khỏi quán, có thể ẩn quán."""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.constants import KetQuaChiTietBaoCao, TrangThaiBaoCao, TrangThaiNoiDung
from app.core.exceptions import AppException, ConflictError, NotFoundError
from app.models.bao_cao import BaoCao
from app.models.nguoi_dung import NguoiDung
from app.repositories import bao_cao_repo, dia_diem_repo, nguoi_dung_repo
from app.schemas.bao_cao import (
    BaoCaoOut,
    ChiTietBaoCaoOut,
    DiaDiemBaoCaoOut,
    GuiBaoCao,
    MonBaoCaoOut,
    NguoiBaoCaoOut,
    XuLyBaoCao,
)
from app.schemas.common import Page
from app.services import dia_diem_service


def _outs(db: Session, ds: list[BaoCao], la_admin: bool) -> list[BaoCaoOut]:
    chi_tiet = bao_cao_repo.chi_tiet_of(db, [bc.idBaoCao for bc in ds])
    ket_qua = []
    for bc in ds:
        dd = dia_diem_repo.get_by_id(db, bc.idDiaDiem)
        nguoi = nguoi_dung_repo.get_by_id(db, bc.idNguoiDung) if la_admin else None
        ket_qua.append(
            BaoCaoOut(
                idBaoCao=bc.idBaoCao,
                diaDiem=DiaDiemBaoCaoOut(idDiaDiem=dd.idDiaDiem, tenDiaDiem=dd.tenDiaDiem, trangThai=dd.trangThai),
                nguoiBaoCao=NguoiBaoCaoOut(idNguoiDung=nguoi.idNguoiDung, hoTen=nguoi.hoTen, email=nguoi.email)
                if nguoi
                else None,
                lyDo=bc.lyDo,
                moTa=bc.moTa,
                trangThai=bc.trangThai,
                ketQuaXuLy=bc.ketQuaXuLy,
                xuLyLuc=bc.xuLyLuc,
                ngayTao=bc.ngayTao,
                chiTiet=[
                    ChiTietBaoCaoOut(
                        idChiTietBaoCao=ct.idChiTietBaoCao,
                        monAn=MonBaoCaoOut(idMonAn=mon.idMonAn, tenMon=mon.tenMon),
                        ketQuaXuLy=ct.ketQuaXuLy or KetQuaChiTietBaoCao.CHO_XU_LY,
                    )
                    for ct, mon in chi_tiet.get(bc.idBaoCao, [])
                ],
            )
        )
    return ket_qua


def gui(db: Session, user: NguoiDung, body: GuiBaoCao) -> BaoCaoOut:
    dd = dia_diem_service.get_active(db, body.idDiaDiem)
    if bao_cao_repo.co_bao_cao_dang_cho(db, user.idNguoiDung, dd.idDiaDiem):
        raise ConflictError("Bạn đã có báo cáo về địa điểm này đang chờ xử lý", "BAO_CAO_DANG_CHO")
    for id_mon in body.idMonAn:
        if dia_diem_repo.get_link(db, id_mon, dd.idDiaDiem) is None:
            raise AppException("MON_KHONG_THUOC_QUAN", "Món được báo cáo không có trong thực đơn của quán", 400)
    bc = bao_cao_repo.create(
        db,
        idNguoiDung=user.idNguoiDung,
        idDiaDiem=dd.idDiaDiem,
        lyDo=body.lyDo.strip(),
        moTa=body.moTa,
        trangThai=TrangThaiBaoCao.CHO_XU_LY.value,
    )
    bao_cao_repo.add_chi_tiet(db, bc.idBaoCao, body.idMonAn)
    db.commit()
    db.refresh(bc)
    return _outs(db, [bc], la_admin=False)[0]


def list_cua_toi(db: Session, user: NguoiDung, page: int, size: int) -> Page[BaoCaoOut]:
    items, total = bao_cao_repo.search(db, id_nguoi_dung=user.idNguoiDung, page=page, size=size)
    return Page[BaoCaoOut](items=_outs(db, items, la_admin=False), total=total, page=page, size=size)


def list_admin(db: Session, trang_thai: str | None, page: int, size: int) -> Page[BaoCaoOut]:
    items, total = bao_cao_repo.search(db, trang_thai=trang_thai, page=page, size=size)
    return Page[BaoCaoOut](items=_outs(db, items, la_admin=True), total=total, page=page, size=size)


def _get(db: Session, id_bao_cao: uuid.UUID) -> BaoCao:
    bc = bao_cao_repo.get_by_id(db, id_bao_cao)
    if not bc:
        raise NotFoundError("Không tìm thấy báo cáo", "BAO_CAO_NOT_FOUND")
    return bc


def get_admin(db: Session, id_bao_cao: uuid.UUID) -> BaoCaoOut:
    return _outs(db, [_get(db, id_bao_cao)], la_admin=True)[0]


def xu_ly(db: Session, id_bao_cao: uuid.UUID, body: XuLyBaoCao) -> BaoCaoOut:
    bc = _get(db, id_bao_cao)
    if bc.trangThai != TrangThaiBaoCao.CHO_XU_LY.value:
        raise ConflictError("Báo cáo đã được xử lý", "BAO_CAO_DA_XU_LY")
    chi_tiet = {ct.idChiTietBaoCao: ct for ct, _ in bao_cao_repo.chi_tiet_of(db, [bc.idBaoCao]).get(bc.idBaoCao, [])}
    ket_qua = {k.idChiTietBaoCao: k.ketQua for k in body.chiTiet}
    if set(ket_qua) != set(chi_tiet):
        raise AppException("KET_QUA_KHONG_KHOP", "Cần gửi kết quả cho đúng và đủ các món trong báo cáo", 400)

    for id_ct, kq in ket_qua.items():
        ct = chi_tiet[id_ct]
        ct.ketQuaXuLy = kq.value
        if kq == KetQuaChiTietBaoCao.VI_PHAM:
            # gỡ món khỏi quán; bao_cao_repo.mon_bi_go chặn pipeline gắn lại
            dia_diem_repo.unlink_mon(db, ct.idMonAn, bc.idDiaDiem)
    if body.anQuan:
        dia_diem_repo.get_by_id(db, bc.idDiaDiem).trangThai = TrangThaiNoiDung.HIDDEN.value
    bc.trangThai = TrangThaiBaoCao.DA_XU_LY.value
    bc.ketQuaXuLy = body.ketQuaXuLy
    bc.xuLyLuc = datetime.now()
    db.commit()
    db.refresh(bc)
    return _outs(db, [bc], la_admin=True)[0]
