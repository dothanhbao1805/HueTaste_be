import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.yeu_thich import DoiTuong


class VietDanhGia(DoiTuong):
    diemSo: int = Field(ge=1, le=5)
    noiDung: str | None = Field(default=None, max_length=2000)


class NguoiVietOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idNguoiDung: uuid.UUID
    hoTen: str
    anhDaiDien: str | None = None


class DanhGiaOut(BaseModel):
    idDanhGia: uuid.UUID
    idMonAn: uuid.UUID | None = None
    idDiaDiem: uuid.UUID | None = None
    diemSo: int
    noiDung: str | None = None
    ngayTao: datetime
    nguoiDung: NguoiVietOut


class TrangDanhGiaOut(BaseModel):
    items: list[DanhGiaOut]
    total: int
    page: int
    size: int
    diemTrungBinh: float | None = Field(
        default=None, description="Món: TB đánh giá app. Quán: gộp rating Google với đánh giá app"
    )
