"""Danh sách món ăn / địa điểm yêu thích của người dùng."""
import uuid

from sqlalchemy.orm import Session

from app.core.constants import LoaiGoiY
from app.core.exceptions import NotFoundError
from app.models.nguoi_dung import NguoiDung
from app.repositories import yeu_thich_repo
from app.schemas.mon_an import MonAnOut
from app.schemas.yeu_thich import ThemYeuThich, YeuThichOut
from app.services import dia_diem_service, mon_an_service


def list_cua_toi(db: Session, user: NguoiDung, loai: LoaiGoiY | None) -> YeuThichOut:
    out = YeuThichOut()
    if loai in (None, LoaiGoiY.MON_AN):
        out.monAn = [MonAnOut.model_validate(m) for m in yeu_thich_repo.list_mon(db, user.idNguoiDung)]
    if loai in (None, LoaiGoiY.DIA_DIEM):
        out.diaDiem = [dia_diem_service.dia_diem_out(dd) for dd in yeu_thich_repo.list_quan(db, user.idNguoiDung)]
    return out


def them(db: Session, user: NguoiDung, body: ThemYeuThich) -> None:
    """Idempotent: đã có thì thôi, app bấm trái tim nhiều lần không bị lỗi."""
    if body.idMonAn:
        mon_an_service.get_active(db, body.idMonAn)
    else:
        dia_diem_service.get_active(db, body.idDiaDiem)
    if yeu_thich_repo.get(db, user.idNguoiDung, id_mon=body.idMonAn, id_dia_diem=body.idDiaDiem) is None:
        yeu_thich_repo.create(db, idNguoiDung=user.idNguoiDung, idMonAn=body.idMonAn, idDiaDiem=body.idDiaDiem)
        db.commit()


def xoa(db: Session, user: NguoiDung, *, id_mon: uuid.UUID | None = None, id_dia_diem: uuid.UUID | None = None) -> None:
    yt = yeu_thich_repo.get(db, user.idNguoiDung, id_mon=id_mon, id_dia_diem=id_dia_diem)
    if yt is None:
        raise NotFoundError("Không có trong danh sách yêu thích", "YEU_THICH_NOT_FOUND")
    yeu_thich_repo.delete(db, yt)
    db.commit()

