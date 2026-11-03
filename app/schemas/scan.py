import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.mon_an import MonAnChiTietOut, MonAnOut


class TrangThaiScan(StrEnum):
    CO_TRONG_HE_THONG = "CO_TRONG_HE_THONG"  # món active -> có monAn (trang chi tiết)
    DANG_CAP_NHAT = "DANG_CAP_NHAT"  # món Huế mới, đang tìm hiểu nền -> app gọi lại GET /scan/{id}
    CHUA_XAC_MINH = "CHUA_XAC_MINH"  # đã tìm hiểu nhưng không xác minh được -> chỉ thông tin cơ bản
    KHONG_LUU = "KHONG_LUU"  # không phải món đặc trưng Huế -> không lưu DB


class ScanOut(BaseModel):
    idLichSuScan: uuid.UUID
    trangThai: TrangThaiScan
    duongDanAnh: str
    tenMonNhanDien: str
    doTinCay: float | None = Field(default=None, description="Model tự đánh giá 0..1, chỉ tham khảo")
    moTaNgan: str | None = None
    laMonDacTrungHue: bool
    idMonAn: uuid.UUID | None = None
    monAn: MonAnChiTietOut | None = None
    monTuongTu: list[MonAnOut] = []


class LichSuScanOut(BaseModel):
    idLichSuScan: uuid.UUID
    duongDanAnh: str
    tenMonNhanDien: str | None = None
    doTinCay: float | None = None
    idMonAn: uuid.UUID | None = None
    ngayTao: datetime


class MonScanKhongLuuOut(BaseModel):
    tenMon: str
    soLanScan: int
    soNguoiScan: int
    lanCuoi: datetime
