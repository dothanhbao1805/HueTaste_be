import uuid
from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.goi_y import _BUA_AN_HOP_LE
from app.schemas.mon_an import NguyenLieuItemOut, _so_nguyen


class CapNhatNhuCau(BaseModel):
    ngay: date | None = Field(default=None, description="Mặc định hôm nay (giờ Việt Nam)")
    buaAn: str = Field(description="sang | trua | chieu | toi | khuya | an_vat")
    gioAn: time | None = Field(default=None, description="Giờ dự định ăn bữa này, vd 06:30")
    nganSach: int | None = Field(default=None, ge=0, le=10_000_000, description="VND")
    ghiChu: str | None = Field(default=None, max_length=500)
    nguyenLieuTranh: list[uuid.UUID] = Field(
        default=[], max_length=30, description="idNguyenLieu cần tránh (lấy từ GET /nguyen-lieu)"
    )

    @field_validator("buaAn")
    @classmethod
    def _bua_an(cls, v: str) -> str:
        if v not in _BUA_AN_HOP_LE:
            raise ValueError(f"buaAn phải là một trong {sorted(_BUA_AN_HOP_LE)}")
        return v

    @field_validator("nguyenLieuTranh")
    @classmethod
    def _bo_trung(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        return list(dict.fromkeys(v))


class NhuCauOut(BaseModel):
    idNhuCauTheoNgay: uuid.UUID
    ngay: date
    buaAn: str | None = None
    gioAn: time | None = None
    nganSach: int | None = None
    ghiChu: str | None = None
    nguyenLieuTranh: list[NguyenLieuItemOut] = []
    ngayCapNhat: datetime

    @field_validator("nganSach", mode="before")
    @classmethod
    def _ngan_sach(cls, v: Any) -> int | None:
        return _so_nguyen(v)
