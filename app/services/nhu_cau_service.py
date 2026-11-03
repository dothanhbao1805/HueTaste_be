"""Nhu cầu ăn uống theo ngày: người dùng đặt trước giờ ăn, ngân sách, ghi chú, nguyên liệu cần tránh
cho từng bữa; /goi-y dùng lại."""
import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import AppException, NotFoundError
from app.models.nguoi_dung import NguoiDung
from app.models.nhu_cau_theo_ngay import NhuCauTheoNgay
from app.repositories import nguyen_lieu_repo, nhu_cau_repo
from app.schemas.mon_an import NguyenLieuItemOut
from app.schemas.nhu_cau import CapNhatNhuCau, NhuCauOut
from app.services.ngu_canh_service import TZ_VN


def _hom_nay() -> date:
    return datetime.now(TZ_VN).date()


def _to_out(db: Session, ds: list[NhuCauTheoNgay]) -> list[NhuCauOut]:
    ids_theo_nc = {nc.idNhuCauTheoNgay: nhu_cau_repo.tach_ids(nc.nguyenLieuTranh) for nc in ds}
    nl = {
        x.idNguyenLieu: NguyenLieuItemOut.model_validate(x)
        for x in nguyen_lieu_repo.get_many(db, list({i for ids in ids_theo_nc.values() for i in ids}))
    }
    return [
        NhuCauOut(
            idNhuCauTheoNgay=nc.idNhuCauTheoNgay,
            ngay=nc.ngay,
            buaAn=nc.buaAn,
            gioAn=nc.gioAn,
            nganSach=nc.nganSach,
            ghiChu=nc.ghiChu,
            nguyenLieuTranh=[nl[i] for i in ids_theo_nc[nc.idNhuCauTheoNgay] if i in nl],
            ngayCapNhat=nc.ngayCapNhat,
        )
        for nc in ds
    ]


def list_cua_toi(db: Session, user: NguoiDung, ngay: date | None) -> list[NhuCauOut]:
    return _to_out(db, nhu_cau_repo.list_theo_ngay(db, user.idNguoiDung, ngay or _hom_nay()))


def cap_nhat(db: Session, user: NguoiDung, body: CapNhatNhuCau) -> NhuCauOut:
    if len(nguyen_lieu_repo.get_many(db, body.nguyenLieuTranh)) != len(body.nguyenLieuTranh):
        raise AppException("NGUYEN_LIEU_NOT_FOUND", "Có nguyên liệu cần tránh không tồn tại")
    nc = nhu_cau_repo.upsert(
        db,
        user.idNguoiDung,
        body.ngay or _hom_nay(),
        body.buaAn,
        gioAn=body.gioAn,
        nganSach=body.nganSach,
        ghiChu=body.ghiChu,
        nguyenLieuTranh=nhu_cau_repo.ghep_ids(body.nguyenLieuTranh),
    )
    db.commit()
    db.refresh(nc)
    return _to_out(db, [nc])[0]


def xoa(db: Session, user: NguoiDung, id_nhu_cau: uuid.UUID) -> None:
    nc = nhu_cau_repo.get_by_id(db, id_nhu_cau)
    if not nc or nc.idNguoiDung != user.idNguoiDung:
        raise NotFoundError("Không tìm thấy nhu cầu", "NHU_CAU_NOT_FOUND")
    nhu_cau_repo.delete(db, nc)  # NguCanh.idNhuCauTheoNgay tự về NULL (FK SET NULL)
    db.commit()
