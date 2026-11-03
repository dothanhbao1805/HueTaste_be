import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import BUA_AN_VAT, Buoi
from app.schemas.mon_an import DiaDiemOut, MonAnOut

_BUA_AN_HOP_LE = {b.value for b in Buoi} | {BUA_AN_VAT}


class YeuCauGoiY(BaseModel):
    viDo: float | None = Field(default=None, ge=-90, le=90)
    kinhDo: float | None = Field(default=None, ge=-180, le=180)
    buaAn: str | None = Field(default=None, description="sang | trua | chieu | toi | khuya | an_vat")
    nganSach: int | None = Field(default=None, ge=0, le=10_000_000, description="VND")
    ghiChu: str | None = Field(default=None, max_length=500)
    nguyenLieuTranh: list[uuid.UUID] | None = Field(
        default=None, max_length=30, description="idNguyenLieu cần tránh; bỏ trống thì dùng nhu cầu đã lưu"
    )
    soMon: int = Field(default=10, ge=1, le=30)
    soDiaDiem: int = Field(default=10, ge=0, le=30)

    @field_validator("buaAn")
    @classmethod
    def _bua_an(cls, v: str | None) -> str | None:
        if v is not None and v not in _BUA_AN_HOP_LE:
            raise ValueError(f"buaAn phải là một trong {sorted(_BUA_AN_HOP_LE)}")
        return v


class NguCanhOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idNguCanh: uuid.UUID
    buoiTrongNgay: str | None = None
    thoiTiet: str | None = None
    nhietDo: float | None = None
    laNgayRam: bool
    viDo: float | None = None
    kinhDo: float | None = None

    @field_validator("nhietDo", "viDo", "kinhDo", mode="before")
    @classmethod
    def _so(cls, v: Any) -> float | None:
        return None if v is None else float(v)


class MonGoiYOut(BaseModel):
    idGoiY: uuid.UUID
    monAn: MonAnOut
    diemSo: float = Field(description="0..1, app hiển thị diemSo*100 = % hợp vị")
    thuHang: int
    lyDoGiaiThich: str


class DiaDiemGoiYOut(BaseModel):
    idGoiY: uuid.UUID
    diaDiem: DiaDiemOut
    diemSo: float
    thuHang: int
    lyDoGiaiThich: str
    monLienQuan: list[MonAnOut] = []


class KetQuaGoiYOut(BaseModel):
    nguCanh: NguCanhOut
    monAn: list[MonGoiYOut]
    diaDiem: list[DiaDiemGoiYOut]
