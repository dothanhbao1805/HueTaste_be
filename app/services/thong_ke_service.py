"""Thống kê tổng quan cho trang admin."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.repositories import bao_cao_repo, thong_ke_repo
from app.schemas.thong_ke import LuotGoiYNgayOut, ThongKeOut, TongQuanOut, TopMonOut
from app.services.ngu_canh_service import TZ_VN

SO_TOP_MON = 10


def tong_quan(db: Session, so_ngay: int, now: datetime | None = None) -> ThongKeOut:
    # DB lưu giờ địa phương không kèm múi giờ (server_default now()) -> so sánh bằng datetime naive giờ VN
    hom_nay = (now or datetime.now(TZ_VN)).date()
    ngay_dau = hom_nay - timedelta(days=so_ngay - 1)
    tu = datetime.combine(ngay_dau, datetime.min.time())

    theo_ngay = thong_ke_repo.luot_goi_y_theo_ngay(db, tu)
    goi_y_theo_ngay = [
        LuotGoiYNgayOut(ngay=d, soLuot=theo_ngay.get(d, 0))
        for d in (ngay_dau + timedelta(days=i) for i in range(so_ngay))
    ]
    return ThongKeOut(
        soNgay=so_ngay,
        tongQuan=TongQuanOut(
            nguoiDung=thong_ke_repo.dem_nguoi_dung(db),
            nguoiDungMoi=thong_ke_repo.dem_nguoi_dung(db, tu),
            monAn=thong_ke_repo.dem_mon_hien_thi(db),
            diaDiem=thong_ke_repo.dem_quan_hien_thi(db),
            danhGia=thong_ke_repo.dem_danh_gia(db),
            baoCaoChoXuLy=bao_cao_repo.dem_cho_xu_ly(db),
            luotGoiY=sum(x.soLuot for x in goi_y_theo_ngay),
        ),
        goiYTheoNgay=goi_y_theo_ngay,
        topMonGoiY=[
            TopMonOut(idMonAn=m.idMonAn, tenMon=m.tenMon, hinhAnh=m.hinhAnh, soLanGoiY=n)
            for m, n in thong_ke_repo.top_mon_goi_y(db, tu, SO_TOP_MON)
        ],
    )
