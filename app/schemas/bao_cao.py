import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.constants import KetQuaChiTietBaoCao, TrangThaiBaoCao


class GuiBaoCao(BaseModel):
    idDiaDiem: uuid.UUID
    lyDo: str = Field(min_length=1, max_length=255)
    moTa: str | None = Field(default=None, max_length=2000)
    idMonAn: list[uuid.UUID] = Field(default=[], max_length=50, description="Món sai/không phù hợp tại quán")

    @field_validator("idMonAn")
    @classmethod
    def _khong_trung(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        return list(dict.fromkeys(v))


class MonBaoCaoOut(BaseModel):
    idMonAn: uuid.UUID
    tenMon: str


class ChiTietBaoCaoOut(BaseModel):
    idChiTietBaoCao: uuid.UUID
    monAn: MonBaoCaoOut
    ketQuaXuLy: KetQuaChiTietBaoCao


class DiaDiemBaoCaoOut(BaseModel):
    idDiaDiem: uuid.UUID
    tenDiaDiem: str
    trangThai: str


class NguoiBaoCaoOut(BaseModel):
    idNguoiDung: uuid.UUID
    hoTen: str
    email: str


class BaoCaoOut(BaseModel):
    idBaoCao: uuid.UUID
    diaDiem: DiaDiemBaoCaoOut
    nguoiBaoCao: NguoiBaoCaoOut | None = None  # chỉ trả cho admin
    lyDo: str
    moTa: str | None = None
    trangThai: TrangThaiBaoCao
    ketQuaXuLy: str | None = None
    xuLyLuc: datetime | None = None
    ngayTao: datetime
    chiTiet: list[ChiTietBaoCaoOut] = []


class KetQuaMonIn(BaseModel):
    idChiTietBaoCao: uuid.UUID
    ketQua: Literal[KetQuaChiTietBaoCao.VI_PHAM, KetQuaChiTietBaoCao.KHONG_VI_PHAM]


class XuLyBaoCao(BaseModel):
    chiTiet: list[KetQuaMonIn] = Field(default=[], description="Phải có kết quả cho mọi món trong báo cáo")
    anQuan: bool = Field(default=False, description="Ẩn luôn địa điểm (DiaDiem.trangThai = hidden)")
    ketQuaXuLy: str | None = Field(default=None, max_length=2000, description="Ghi chú gửi người báo cáo")
