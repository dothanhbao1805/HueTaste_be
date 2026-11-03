from enum import StrEnum


class VaiTro(StrEnum):
    USER = "user"
    ADMIN = "admin"


class TrangThaiNguoiDung(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class TrangThaiNoiDung(StrEnum):
    """Trạng thái MonAn/DiaDiem. `unverified`: pipeline không xác minh được nguồn, không hiển thị."""

    ACTIVE = "active"
    HIDDEN = "hidden"
    UNVERIFIED = "unverified"


class Buoi(StrEnum):
    SANG = "sang"
    TRUA = "trua"
    CHIEU = "chieu"
    TOI = "toi"
    KHUYA = "khuya"


BUA_AN_VAT = "an_vat"  # chip "Ăn vặt" trên Home: không phải buổi, chỉ ưu tiên món ăn vặt/chè/bánh
TEN_BUOI = {
    Buoi.SANG: "bữa sáng",
    Buoi.TRUA: "bữa trưa",
    Buoi.CHIEU: "buổi chiều",
    Buoi.TOI: "bữa tối",
    Buoi.KHUYA: "ăn khuya",
}


class ThoiTiet(StrEnum):
    NONG = "nong"
    MAT = "mat"
    LANH = "lanh"
    MUA = "mua"


class LoaiGoiY(StrEnum):
    MON_AN = "mon_an"
    DIA_DIEM = "dia_diem"


class LoaiSoThich(StrEnum):
    VI = "vi"
    KIEU = "kieu"


class LoaiThuThap(StrEnum):
    MON_AN = "mon_an"
    DIA_DIEM = "dia_diem"
    TAT_CA = "tat_ca"


DANH_MUC_MON = (
    "Bún - Bánh canh - Mì",
    "Bánh Huế",
    "Cơm - Cháo",
    "Chè - Tráng miệng",
    "Ăn vặt",
    "Món chay",
    "Món mặn khác",
)

# Tên tag lưu thẳng vào SoThich.tenSoThich (app hiển thị làm chip). Gemini chỉ được chọn trong các giá trị này.
VI_MON = ("Cay", "Ngọt", "Chua", "Mặn", "Đậm đà", "Thanh đạm", "Béo")
KIEU_MON = ("Món nước", "Món khô", "Bánh", "Chè - tráng miệng", "Ăn vặt", "Cơm", "Đồ uống")

CHE_DO_CHAY = "Ăn chay"
CHE_DO_AN = (CHE_DO_CHAY, "Ít dầu mỡ", "Ít đường", "Không hải sản")


class TrangThaiBaoCao(StrEnum):
    CHO_XU_LY = "CHO_XU_LY"
    DA_XU_LY = "DA_XU_LY"


class KetQuaChiTietBaoCao(StrEnum):
    """ChiTietBaoCao.ketQuaXuLy theo tài liệu. VI_PHAM: gỡ món khỏi quán bị báo cáo."""

    CHO_XU_LY = "CHO_XU_LY"
    VI_PHAM = "VI_PHAM"
    KHONG_VI_PHAM = "KHONG_VI_PHAM"
