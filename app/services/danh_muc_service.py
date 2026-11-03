"""Admin quản lý danh mục món ăn. Pipeline thu thập cũng xếp món vào các danh mục này."""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.danh_muc_mon_an import DanhMucMonAn
from app.repositories import danh_muc_repo
from app.schemas.mon_an import CapNhatDanhMuc, DanhMucAdminOut, TaoDanhMuc


def _out(dm: DanhMucMonAn, so_mon: int) -> DanhMucAdminOut:
    return DanhMucAdminOut(
        idDanhMucMonAn=dm.idDanhMucMonAn,
        tenDanhMuc=dm.tenDanhMuc,
        moTa=dm.moTa,
        soMon=so_mon,
        ngayTao=dm.ngayTao,
        ngayCapNhat=dm.ngayCapNhat,
    )


def _get(db: Session, id_danh_muc: uuid.UUID) -> DanhMucMonAn:
    dm = danh_muc_repo.get_by_id(db, id_danh_muc)
    if not dm:
        raise NotFoundError("Không tìm thấy danh mục", "DANH_MUC_NOT_FOUND")
    return dm


def _kiem_tra_trung_ten(db: Session, ten: str, bo_qua: uuid.UUID | None = None) -> None:
    trung = danh_muc_repo.get_by_ten(db, ten)
    if trung and trung.idDanhMucMonAn != bo_qua:
        raise ConflictError("Tên danh mục đã tồn tại", "DANH_MUC_EXISTS")


def list_admin(db: Session) -> list[DanhMucAdminOut]:
    so_mon = danh_muc_repo.dem_mon(db)
    return [_out(dm, so_mon.get(dm.idDanhMucMonAn, 0)) for dm in danh_muc_repo.list_all(db)]


def create(db: Session, body: TaoDanhMuc) -> DanhMucAdminOut:
    ten = body.tenDanhMuc.strip()
    _kiem_tra_trung_ten(db, ten)
    dm = danh_muc_repo.create(db, tenDanhMuc=ten, moTa=body.moTa)
    db.commit()
    db.refresh(dm)
    return _out(dm, 0)


def update(db: Session, id_danh_muc: uuid.UUID, body: CapNhatDanhMuc) -> DanhMucAdminOut:
    dm = _get(db, id_danh_muc)
    if body.tenDanhMuc is not None:
        ten = body.tenDanhMuc.strip()
        _kiem_tra_trung_ten(db, ten, bo_qua=dm.idDanhMucMonAn)
        dm.tenDanhMuc = ten
    if body.moTa is not None:
        dm.moTa = body.moTa
    db.commit()
    db.refresh(dm)
    return _out(dm, danh_muc_repo.dem_mon(db).get(dm.idDanhMucMonAn, 0))


def delete(db: Session, id_danh_muc: uuid.UUID) -> None:
    dm = _get(db, id_danh_muc)
    if danh_muc_repo.dem_mon(db).get(dm.idDanhMucMonAn, 0):
        # FK MonAn -> DanhMucMonAn là RESTRICT
        raise ConflictError("Danh mục đang có món ăn, không thể xóa", "DANH_MUC_IN_USE")
    danh_muc_repo.delete(db, dm)
    db.commit()
