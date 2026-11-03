import uuid
from datetime import date

from pydantic import BaseModel


class TongQuanOut(BaseModel):
    nguoiDung: int
    nguoiDungMoi: int  # đăng ký trong kỳ thống kê
    monAn: int  # đang hiển thị (active)
    diaDiem: int
    danhGia: int
    baoCaoChoXuLy: int
    luotGoiY: int  # trong kỳ


class LuotGoiYNgayOut(BaseModel):
    ngay: date
    soLuot: int


class TopMonOut(BaseModel):
    idMonAn: uuid.UUID
    tenMon: str
    hinhAnh: str | None = None
    soLanGoiY: int


class ThongKeOut(BaseModel):
    soNgay: int
    tongQuan: TongQuanOut
    goiYTheoNgay: list[LuotGoiYNgayOut]  # đủ từng ngày, ngày không có lượt = 0
    topMonGoiY: list[TopMonOut]
