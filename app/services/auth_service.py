from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.constants import TrangThaiNguoiDung, VaiTro
from app.core.exceptions import AppException, ConflictError, ForbiddenError, UnauthorizedError
from app.models.nguoi_dung import NguoiDung
from app.repositories import nguoi_dung_repo, token_repo
from app.schemas.auth import TokenOut
from app.services import email_service


def _build_tokens(user: NguoiDung) -> TokenOut:
    return TokenOut(
        accessToken=security.create_access_token(user.idNguoiDung),
        refreshToken=security.create_refresh_token(user.idNguoiDung),
        nguoiDung=user,  # type: ignore[arg-type]  # pydantic from_attributes
    )


def register(db: Session, *, email: str, mat_khau: str, ho_ten: str) -> TokenOut:
    email = email.lower()
    if nguoi_dung_repo.get_by_email(db, email):
        raise ConflictError("Email đã được sử dụng", "EMAIL_EXISTS")
    user = nguoi_dung_repo.create(
        db,
        email=email,
        matKhauMaHoa=security.hash_password(mat_khau),
        hoTen=ho_ten.strip(),
        vaiTro=VaiTro.USER.value,
        trangThai=TrangThaiNguoiDung.ACTIVE.value,
    )
    db.commit()
    return _build_tokens(user)


def login(db: Session, *, email: str, mat_khau: str, require_admin: bool = False) -> TokenOut:
    user = nguoi_dung_repo.get_by_email(db, email)
    if not user or not security.verify_password(mat_khau, user.matKhauMaHoa):
        raise UnauthorizedError("Email hoặc mật khẩu không đúng", "INVALID_CREDENTIALS")
    if user.trangThai != TrangThaiNguoiDung.ACTIVE.value:
        raise ForbiddenError("Tài khoản đã bị khóa", "ACCOUNT_BLOCKED")
    if require_admin and user.vaiTro != VaiTro.ADMIN.value:
        raise ForbiddenError("Tài khoản không có quyền quản trị", "NOT_ADMIN")
    return _build_tokens(user)


def refresh(db: Session, *, refresh_token: str) -> TokenOut:
    user_id = security.decode_token(refresh_token, security.REFRESH)
    user = nguoi_dung_repo.get_by_id(db, user_id)
    if not user or user.trangThai != TrangThaiNguoiDung.ACTIVE.value:
        raise UnauthorizedError("Tài khoản không hợp lệ", "INVALID_TOKEN")
    return _build_tokens(user)


def forgot_password(db: Session, *, email: str) -> None:
    """Luôn thành công với caller để không lộ email nào tồn tại."""
    user = nguoi_dung_repo.get_by_email(db, email)
    if not user or user.trangThai != TrangThaiNguoiDung.ACTIVE.value:
        return
    token_repo.invalidate_all_for_user(db, user.idNguoiDung)
    raw, hashed = security.generate_reset_token()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    token_repo.create(db, user.idNguoiDung, hashed, expires)
    db.commit()
    email_service.send_reset_password_email(user.email, raw)


def reset_password(db: Session, *, token: str, mat_khau_moi: str) -> None:
    record = token_repo.get_by_hash(db, security.hash_reset_token(token))
    invalid = AppException("INVALID_RESET_TOKEN", "Token không hợp lệ hoặc đã hết hạn", 400)
    if not record or record.daSuDung:
        raise invalid
    expires = record.hetHanLuc
    if expires.tzinfo is None:  # SQLite trả datetime naive
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise invalid
    user = nguoi_dung_repo.get_by_id(db, record.idNguoiDung)
    if not user:
        raise invalid
    user.matKhauMaHoa = security.hash_password(mat_khau_moi)
    record.daSuDung = True
    db.commit()
