import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _csv_sang_list(v: Any) -> list[str]:
    if v is None or v == "":
        return []
    if isinstance(v, str):
        return [x for x in v.split(",") if x]
    return list(v)


def _so_nguyen(v: Any) -> int | None:
    return None if v is None else int(Decimal(v))


def _so_thuc(v: Any) -> float | None:
    return None if v is None else float(v)


class DanhMucOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idDanhMucMonAn: uuid.UUID
    tenDanhMuc: str
    moTa: str | None = None


class DanhMucAdminOut(DanhMucOut):
    soMon: int = 0
    ngayTao: datetime
    ngayCapNhat: datetime


class TaoDanhMuc(BaseModel):
    tenDanhMuc: str = Field(min_length=1, max_length=150)
    moTa: str | None = Field(default=None, max_length=2000)


class CapNhatDanhMuc(BaseModel):
    tenDanhMuc: str | None = Field(default=None, min_length=1, max_length=150)
    moTa: str | None = Field(default=None, max_length=2000)


class SoThichOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idSoThich: uuid.UUID
    loai: str
    tenSoThich: str


class CheDoAnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idCheDoAn: uuid.UUID
    tenCheDo: str
    moTa: str | None = None


class MonAnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idMonAn: uuid.UUID
    idDanhMucMonAn: uuid.UUID
    tenMon: str
    moTa: str | None = None
    hinhAnh: str | None = None
    buoiPhuHop: list[str] = []
    thoiTietPhuHop: list[str] = []
    giaThamKhaoTu: int | None = None
    giaThamKhaoDen: int | None = None
    nguonThamKhao: str | None = None

    _csv = field_validator("buoiPhuHop", "thoiTietPhuHop", mode="before")(_csv_sang_list)
    _gia = field_validator("giaThamKhaoTu", "giaThamKhaoDen", mode="before")(_so_nguyen)


class NguyenLieuItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idNguyenLieu: uuid.UUID
    tenNguyenLieu: str
    nhomNguyenLieu: str | None = None


class NguyenLieuOut(BaseModel):
    idNguyenLieu: uuid.UUID
    tenNguyenLieu: str
    nhomNguyenLieu: str | None = None
    laThanhPhanChinh: bool


class TagMonOut(SoThichOut):
    trongSo: float


class DiaDiemOut(BaseModel):
    idDiaDiem: uuid.UUID
    tenDiaDiem: str
    diaChi: str | None = None
    viDo: float | None = None
    kinhDo: float | None = None
    soDienThoai: str | None = None
    gioMoCua: list[str] = []
    mucGia: int | None = None
    diemTrungBinh: float | None = None
    anhUrl: str | None = None
    khoangCachKm: float | None = None

    _thuc = field_validator("viDo", "kinhDo", "diemTrungBinh", mode="before")(_so_thuc)

    @field_validator("gioMoCua", mode="before")
    @classmethod
    def _gio(cls, v: Any) -> list[str]:
        if not v:
            return []
        return json.loads(v) if isinstance(v, str) else list(v)


class QuanBanMonOut(BaseModel):
    diaDiem: DiaDiemOut
    giaBan: int | None = None
    laMonDacTrung: bool


class MonTaiQuanOut(BaseModel):
    monAn: MonAnOut
    giaBan: int | None = None
    laMonDacTrung: bool


class AnhOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url: str
    urlThumbnail: str | None = None
    nguon: str | None = None


class MonAnChiTietOut(MonAnOut):
    anh: list[AnhOut] = []
    danhMuc: DanhMucOut | None = None
    nguyenLieu: list[NguyenLieuOut] = []
    soThich: list[TagMonOut] = []
    cheDoAn: list[CheDoAnOut] = []
    diaDiem: list[QuanBanMonOut] = []
    daYeuThich: bool = False


class DiaDiemChiTietOut(DiaDiemOut):
    maGooglePlace: str | None = None
    anh: list[AnhOut] = []
    monAn: list[MonTaiQuanOut] = []
    daYeuThich: bool = False


class SoThichNguoiDungIn(BaseModel):
    idSoThich: uuid.UUID
    mucDo: int = Field(default=3, ge=1, le=5)


class CapNhatSoThich(BaseModel):
    soThich: list[SoThichNguoiDungIn] = Field(default=[], max_length=50)


class SoThichNguoiDungOut(SoThichOut):
    mucDo: int


class CheDoAnNguoiDungIn(BaseModel):
    idCheDoAn: uuid.UUID
    ghiChu: str | None = Field(default=None, max_length=255)


class CapNhatCheDoAn(BaseModel):
    cheDoAn: list[CheDoAnNguoiDungIn] = Field(default=[], max_length=20)


class CheDoAnNguoiDungOut(CheDoAnOut):
    ghiChu: str | None = None
