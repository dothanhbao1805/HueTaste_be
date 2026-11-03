import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.constants import TrangThaiNguoiDung, VaiTro


class NguoiDungOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idNguoiDung: uuid.UUID
    email: EmailStr
    hoTen: str
    anhDaiDien: str | None = None
    vaiTro: VaiTro
    trangThai: TrangThaiNguoiDung
    ngayTao: datetime
    ngayCapNhat: datetime


class CapNhatThongTin(BaseModel):
    hoTen: str | None = Field(default=None, min_length=1, max_length=150)
    anhDaiDien: str | None = None


class DoiMatKhau(BaseModel):
    matKhauCu: str
    matKhauMoi: str = Field(min_length=8, max_length=128)


class CapNhatTrangThai(BaseModel):
    trangThai: TrangThaiNguoiDung
