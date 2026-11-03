from pydantic import BaseModel, EmailStr, Field

from app.schemas.nguoi_dung import NguoiDungOut


class DangKy(BaseModel):
    email: EmailStr
    matKhau: str = Field(min_length=8, max_length=128)
    hoTen: str = Field(min_length=1, max_length=150)


class DangNhap(BaseModel):
    email: EmailStr
    matKhau: str


class RefreshRequest(BaseModel):
    refreshToken: str


class TokenOut(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    nguoiDung: NguoiDungOut


class QuenMatKhau(BaseModel):
    email: EmailStr


class DatLaiMatKhau(BaseModel):
    token: str
    matKhauMoi: str = Field(min_length=8, max_length=128)
