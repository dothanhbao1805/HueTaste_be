from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.schemas.auth import DangKy, DangNhap, DatLaiMatKhau, QuenMatKhau, RefreshRequest, TokenOut
from app.schemas.common import Message
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: DangKy, db: DbSession):
    return auth_service.register(db, email=body.email, mat_khau=body.matKhau, ho_ten=body.hoTen)


@router.post("/login", response_model=TokenOut)
def login(body: DangNhap, db: DbSession):
    return auth_service.login(db, email=body.email, mat_khau=body.matKhau)


@router.post("/admin/login", response_model=TokenOut)
def admin_login(body: DangNhap, db: DbSession):
    return auth_service.login(db, email=body.email, mat_khau=body.matKhau, require_admin=True)


@router.post("/refresh", response_model=TokenOut)
def refresh(body: RefreshRequest, db: DbSession):
    return auth_service.refresh(db, refresh_token=body.refreshToken)


@router.post("/forgot-password", response_model=Message)
def forgot_password(body: QuenMatKhau, db: DbSession):
    auth_service.forgot_password(db, email=body.email)
    return Message(message="Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi")


@router.post("/reset-password", response_model=Message)
def reset_password(body: DatLaiMatKhau, db: DbSession):
    auth_service.reset_password(db, token=body.token, mat_khau_moi=body.matKhauMoi)
    return Message(message="Đặt lại mật khẩu thành công")
