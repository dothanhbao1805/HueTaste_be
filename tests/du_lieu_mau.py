"""Dữ liệu mẫu nhỏ cho test API tra cứu và gợi ý."""
from decimal import Decimal

from app.core.chuan_hoa import chuan_hoa_ten
from app.models import (
    CheDoAn,
    DanhMucMonAn,
    DiaDiem,
    MonAn,
    MonAnCheDoAn,
    MonAnDiaDiem,
    MonAnNguyenLieu,
    MonAnSoThich,
    NguyenLieu,
    SoThich,
)


def _mon(dm, ten, buoi, thoi_tiet, gia, trang_thai="active"):
    return MonAn(
        idDanhMucMonAn=dm.idDanhMucMonAn,
        tenMon=ten,
        tenChuanHoa=chuan_hoa_ten(ten),
        buoiPhuHop=buoi,
        thoiTietPhuHop=thoi_tiet,
        giaThamKhaoTu=Decimal(gia),
        trangThai=trang_thai,
    )


def tao_du_lieu(db) -> dict:
    bun = DanhMucMonAn(tenDanhMuc="Bún - Bánh canh - Mì")
    banh = DanhMucMonAn(tenDanhMuc="Bánh Huế")
    che = DanhMucMonAn(tenDanhMuc="Chè - Tráng miệng")
    db.add_all([bun, banh, che])
    db.flush()

    bun_bo = _mon(bun, "Bún bò Huế", "sang,trua", "lanh,mua", 40000)
    banh_beo = _mon(banh, "Bánh bèo", "sang,chieu", "mat", 25000)
    che_chay = _mon(che, "Chè bắp", "chieu,toi", "nong,mat", 15000)
    bi_an = _mon(bun, "Món chưa xác minh", "sang", "lanh", 10000, trang_thai="unverified")
    db.add_all([bun_bo, banh_beo, che_chay, bi_an])

    cay = SoThich(loai="vi", tenSoThich="Cay")
    ngot = SoThich(loai="vi", tenSoThich="Ngọt")
    mon_nuoc = SoThich(loai="kieu", tenSoThich="Món nước")
    chay = CheDoAn(tenCheDo="Ăn chay")
    thit_bo = NguyenLieu(tenNguyenLieu="Thịt bò", nhomNguyenLieu="thịt")
    tom = NguyenLieu(tenNguyenLieu="Tôm", nhomNguyenLieu="hải sản")
    db.add_all([cay, ngot, mon_nuoc, chay, thit_bo, tom])
    db.flush()

    db.add_all(
        [
            MonAnSoThich(idMonAn=bun_bo.idMonAn, idSoThich=cay.idSoThich, trongSo=Decimal("0.9")),
            MonAnSoThich(idMonAn=bun_bo.idMonAn, idSoThich=mon_nuoc.idSoThich, trongSo=Decimal("1")),
            MonAnSoThich(idMonAn=che_chay.idMonAn, idSoThich=ngot.idSoThich, trongSo=Decimal("1")),
            MonAnCheDoAn(idMonAn=che_chay.idMonAn, idCheDoAn=chay.idCheDoAn),
            MonAnNguyenLieu(idMonAn=bun_bo.idMonAn, idNguyenLieu=thit_bo.idNguyenLieu, laThanhPhanChinh=True),
            MonAnNguyenLieu(idMonAn=banh_beo.idMonAn, idNguyenLieu=tom.idNguyenLieu, laThanhPhanChinh=True),
        ]
    )
    # Quán gần Cầu Tràng Tiền (16.4637, 107.5909) và một quán xa ~3km
    gan = DiaDiem(
        tenDiaDiem="Bún bò O Phượng", viDo=Decimal("16.4650"), kinhDo=Decimal("107.5920"),
        diemTrungBinh=Decimal("4.7"), mucGia=1, trangThai="active", maGooglePlace="p_gan",
    )
    xa = DiaDiem(
        tenDiaDiem="Bánh bèo Bà Đỏ", viDo=Decimal("16.4900"), kinhDo=Decimal("107.5700"),
        diemTrungBinh=Decimal("4.2"), mucGia=1, trangThai="active", maGooglePlace="p_xa",
        hinhAnh="https://lh5.googleusercontent.com/p_xa",
    )
    db.add_all([gan, xa])
    db.flush()
    db.add_all(
        [
            MonAnDiaDiem(idMonAn=bun_bo.idMonAn, idDiaDiem=gan.idDiaDiem, laMonDacTrung=True, giaBan=Decimal(40000)),
            MonAnDiaDiem(idMonAn=banh_beo.idMonAn, idDiaDiem=xa.idDiaDiem, laMonDacTrung=True),
            MonAnDiaDiem(idMonAn=banh_beo.idMonAn, idDiaDiem=gan.idDiaDiem, laMonDacTrung=False),
        ]
    )
    db.commit()
    return {
        "bun_bo": bun_bo, "banh_beo": banh_beo, "che_chay": che_chay, "bi_an": bi_an,
        "cay": cay, "ngot": ngot, "chay": chay, "gan": gan, "xa": xa,
        "thit_bo": thit_bo, "tom": tom,
    }
