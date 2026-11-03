from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.constants import TrangThaiNguoiDung, VaiTro
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.models.nguoi_dung import NguoiDung
from app.repositories import nguoi_dung_repo

bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> NguoiDung:
    if creds is None:
        raise UnauthorizedError("Thiếu access token")
    user_id = security.decode_token(creds.credentials, security.ACCESS)
    user = nguoi_dung_repo.get_by_id(db, user_id)
    if not user:
        raise UnauthorizedError("Người dùng không tồn tại", "INVALID_TOKEN")
    if user.trangThai != TrangThaiNguoiDung.ACTIVE.value:
        raise ForbiddenError("Tài khoản đã bị khóa", "ACCOUNT_BLOCKED")
    return user


def get_optional_user(
    db: DbSession,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> NguoiDung | None:
    """Endpoint công khai nhưng trả thêm thông tin riêng (vd daYeuThich) khi có token hợp lệ."""
    if creds is None:
        return None
    try:
        return get_current_user(db, creds)
    except (UnauthorizedError, ForbiddenError):
        return None


def require_admin(user: Annotated[NguoiDung, Depends(get_current_user)]) -> NguoiDung:
    if user.vaiTro != VaiTro.ADMIN.value:
        raise ForbiddenError("Chỉ quản trị viên mới được truy cập", "NOT_ADMIN")
    return user


CurrentUser = Annotated[NguoiDung, Depends(get_current_user)]
CurrentAdmin = Annotated[NguoiDung, Depends(require_admin)]
OptionalUser = Annotated[NguoiDung | None, Depends(get_optional_user)]
