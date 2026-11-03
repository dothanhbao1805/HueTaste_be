import uuid

from sqlalchemy.orm import Session

from app.core import security
from app.core.exceptions import AppException, NotFoundError
from app.models.nguoi_dung import NguoiDung
from app.repositories import nguoi_dung_repo
from app.schemas.common import Page
from app.schemas.nguoi_dung import NguoiDungOut


def update_profile(db: Session, user: NguoiDung, *, ho_ten: str | None, anh_dai_dien: str | None) -> NguoiDung:
    if ho_ten is not None:
        user.hoTen = ho_ten.strip()
    if anh_dai_dien is not None:
        user.anhDaiDien = anh_dai_dien
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: NguoiDung, *, mat_khau_cu: str, mat_khau_moi: str) -> None:
    if not security.verify_password(mat_khau_cu, user.matKhauMaHoa):
        raise AppException("WRONG_PASSWORD", "Mật khẩu cũ không đúng", 400)
    user.matKhauMaHoa = security.hash_password(mat_khau_moi)
    db.commit()


def list_users(
    db: Session, *, q: str | None, vai_tro: str | None, trang_thai: str | None, page: int, size: int
) -> Page[NguoiDungOut]:
    items, total = nguoi_dung_repo.search(
        db, q=q, vai_tro=vai_tro, trang_thai=trang_thai, page=page, size=size
    )
    return Page[NguoiDungOut](
        items=[NguoiDungOut.model_validate(u) for u in items], total=total, page=page, size=size
    )


def get_user(db: Session, user_id: uuid.UUID) -> NguoiDung:
    user = nguoi_dung_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("Không tìm thấy người dùng", "USER_NOT_FOUND")
    return user


def set_status(db: Session, *, admin: NguoiDung, user_id: uuid.UUID, trang_thai: str) -> NguoiDung:
    user = get_user(db, user_id)
    if user.idNguoiDung == admin.idNguoiDung:
        raise AppException("CANNOT_CHANGE_SELF", "Không thể thay đổi trạng thái của chính mình", 400)
    user.trangThai = trang_thai
    db.commit()
    db.refresh(user)
    return user
