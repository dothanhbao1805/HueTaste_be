"""baseline: toan bo schema huetaste (24 bang)

Khớp với schema đã tạo tay trong MySQL. Với DB `huetaste` đã có sẵn bảng, chỉ cần
`alembic stamp 0001`; DB trống thì `alembic upgrade head`.

Revision ID: 0001
Revises:
Create Date: 2026-10-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.types import UUIDChar36

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_mysql() -> bool:
    # uuid() và ON UPDATE chỉ có ở MySQL; bỏ qua khi chạy trên SQLite (kiểm thử migration)
    return op.get_bind().dialect.name == "mysql"


def _pk(name: str) -> sa.Column:
    default = sa.text("(uuid())") if _is_mysql() else None
    return sa.Column(name, UUIDChar36(), primary_key=True, server_default=default)


def _fk(name: str, ref: str, fk_name: str, ondelete: str = "CASCADE", nullable: bool = False) -> sa.Column:
    return sa.Column(
        name,
        UUIDChar36(),
        sa.ForeignKey(ref, name=fk_name, ondelete=ondelete, onupdate="CASCADE"),
        nullable=nullable,
    )


def _ngay_tao(name: str = "ngayTao") -> sa.Column:
    return sa.Column(name, sa.TIMESTAMP(), nullable=False, server_default=sa.func.now())


def _ngay_cap_nhat() -> sa.Column:
    return sa.Column(
        "ngayCapNhat",
        sa.TIMESTAMP(),
        nullable=False,
        server_default=sa.text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP" if _is_mysql() else "CURRENT_TIMESTAMP"
        ),
    )


def _bool_false(name: str) -> sa.Column:
    return sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.text("0"))


def upgrade() -> None:
    op.create_table(
        "NguoiDung",
        _pk("idNguoiDung"),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("matKhauMaHoa", sa.String(255), nullable=False),
        sa.Column("hoTen", sa.String(150), nullable=False),
        sa.Column("anhDaiDien", sa.Text(), nullable=True),
        sa.Column("vaiTro", sa.String(30), nullable=False),
        sa.Column("trangThai", sa.String(30), nullable=False),
        _ngay_tao(),
        _ngay_cap_nhat(),
        sa.UniqueConstraint("email", name="uq_nguoidung_email"),
    )
    op.create_table(
        "TokenDatLaiMatKhau",
        _pk("idTokenDatLaiMatKhau"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_token_nguoidung"),
        sa.Column("maToken", sa.String(255), nullable=False),
        sa.Column("hetHanLuc", sa.DateTime(), nullable=False),
        _bool_false("daSuDung"),
        _ngay_tao(),
        sa.UniqueConstraint("maToken", name="uq_token_matoken"),
    )
    op.create_table(
        "DanhMucMonAn",
        _pk("idDanhMucMonAn"),
        sa.Column("tenDanhMuc", sa.String(150), nullable=False),
        sa.Column("moTa", sa.Text(), nullable=True),
        _ngay_tao(),
        _ngay_cap_nhat(),
    )
    op.create_table(
        "MonAn",
        _pk("idMonAn"),
        _fk("idDanhMucMonAn", "DanhMucMonAn.idDanhMucMonAn", "fk_monan_danhmuc", ondelete="RESTRICT"),
        sa.Column("tenMon", sa.String(255), nullable=False),
        sa.Column("moTa", sa.Text(), nullable=True),
        sa.Column("hinhAnh", sa.Text(), nullable=True),
        sa.Column("buoiPhuHop", sa.String(50), nullable=True),
        sa.Column("thoiTietPhuHop", sa.String(50), nullable=True),
        sa.Column("giaThamKhaoTu", sa.Numeric(12, 0), nullable=True),
        sa.Column("giaThamKhaoDen", sa.Numeric(12, 0), nullable=True),
        sa.Column("trangThai", sa.String(30), nullable=False),
        _ngay_tao(),
        _ngay_cap_nhat(),
    )
    op.create_table(
        "NguyenLieu",
        _pk("idNguyenLieu"),
        sa.Column("tenNguyenLieu", sa.String(150), nullable=False),
        sa.Column("nhomNguyenLieu", sa.String(100), nullable=True),
    )
    op.create_table(
        "MonAnNguyenLieu",
        _pk("idMonAnNguyenLieu"),
        _fk("idMonAn", "MonAn.idMonAn", "fk_mannl_monan"),
        _fk("idNguyenLieu", "NguyenLieu.idNguyenLieu", "fk_mannl_nguyenlieu"),
        _bool_false("laThanhPhanChinh"),
        sa.UniqueConstraint("idMonAn", "idNguyenLieu", name="uq_monan_nguyenlieu"),
    )
    op.create_table(
        "DiaDiem",
        _pk("idDiaDiem"),
        sa.Column("maGooglePlace", sa.String(255), nullable=True),
        sa.Column("tenDiaDiem", sa.String(255), nullable=False),
        sa.Column("diaChi", sa.Text(), nullable=True),
        sa.Column("viDo", sa.Numeric(10, 7), nullable=True),
        sa.Column("kinhDo", sa.Numeric(10, 7), nullable=True),
        sa.Column("soDienThoai", sa.String(20), nullable=True),
        sa.Column("gioMoCua", sa.Text(), nullable=True),
        sa.Column("mucGia", sa.Integer(), nullable=True),
        sa.Column("diemTrungBinh", sa.Numeric(3, 2), nullable=True),
        sa.Column("hinhAnh", sa.Text(), nullable=True),
        sa.Column("trangThai", sa.String(30), nullable=False),
        _ngay_tao(),
        _ngay_cap_nhat(),
        sa.UniqueConstraint("maGooglePlace", name="uq_diadiem_googleplace"),
    )
    op.create_table(
        "MonAnDiaDiem",
        _pk("idMonAnDiaDiem"),
        _fk("idMonAn", "MonAn.idMonAn", "fk_madd_monan"),
        _fk("idDiaDiem", "DiaDiem.idDiaDiem", "fk_madd_diadiem"),
        sa.Column("giaBan", sa.Numeric(12, 0), nullable=True),
        _bool_false("laMonDacTrung"),
        sa.UniqueConstraint("idMonAn", "idDiaDiem", name="uq_monan_diadiem"),
    )
    op.create_table(
        "CheDoAn",
        _pk("idCheDoAn"),
        sa.Column("tenCheDo", sa.String(150), nullable=False),
        sa.Column("moTa", sa.Text(), nullable=True),
    )
    op.create_table(
        "MonAnCheDoAn",
        _pk("idMonAnCheDoAn"),
        _fk("idMonAn", "MonAn.idMonAn", "fk_macd_monan"),
        _fk("idCheDoAn", "CheDoAn.idCheDoAn", "fk_macd_chedoan"),
        sa.UniqueConstraint("idMonAn", "idCheDoAn", name="uq_monan_chedoan"),
    )
    op.create_table(
        "CheDoAnNguoiDung",
        _pk("idCheDoAnNguoiDung"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_cdand_nguoidung"),
        _fk("idCheDoAn", "CheDoAn.idCheDoAn", "fk_cdand_chedoan"),
        sa.Column("ghiChu", sa.String(255), nullable=True),
        sa.UniqueConstraint("idNguoiDung", "idCheDoAn", name="uq_user_chedoan"),
    )
    op.create_table(
        "SoThich",
        _pk("idSoThich"),
        sa.Column("loai", sa.String(50), nullable=False),
        sa.Column("tenSoThich", sa.String(150), nullable=False),
    )
    op.create_table(
        "MonAnSoThich",
        _pk("idMonAnSoThich"),
        _fk("idMonAn", "MonAn.idMonAn", "fk_mast_monan"),
        _fk("idSoThich", "SoThich.idSoThich", "fk_mast_sothich"),
        sa.Column("trongSo", sa.Numeric(5, 2), nullable=False, server_default=sa.text("1.00")),
        sa.UniqueConstraint("idMonAn", "idSoThich", name="uq_monan_sothich"),
    )
    op.create_table(
        "SoThichNguoiDung",
        _pk("idSoThichNguoiDung"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_stnd_nguoidung"),
        _fk("idSoThich", "SoThich.idSoThich", "fk_stnd_sothich"),
        sa.Column("mucDo", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.UniqueConstraint("idNguoiDung", "idSoThich", name="uq_user_sothich"),
        sa.CheckConstraint("mucDo between 1 and 5", name="chk_stnd_mucdo"),
    )
    op.create_table(
        "NhuCauTheoNgay",
        _pk("idNhuCauTheoNgay"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_nc_nguoidung"),
        sa.Column("ngay", sa.Date(), nullable=False),
        sa.Column("buaAn", sa.String(50), nullable=True),
        sa.Column("nganSach", sa.Numeric(12, 0), nullable=True),
        sa.Column("ghiChu", sa.String(500), nullable=True),
        _ngay_tao(),
        _ngay_cap_nhat(),
    )
    op.create_table(
        "NguCanh",
        _pk("idNguCanh"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_nguc_nguoidung"),
        _fk(
            "idNhuCauTheoNgay",
            "NhuCauTheoNgay.idNhuCauTheoNgay",
            "fk_nguc_nhucau",
            ondelete="SET NULL",
            nullable=True,
        ),
        sa.Column("viDo", sa.Numeric(10, 7), nullable=True),
        sa.Column("kinhDo", sa.Numeric(10, 7), nullable=True),
        sa.Column("nhietDo", sa.Numeric(5, 2), nullable=True),
        sa.Column("thoiTiet", sa.String(50), nullable=True),
        sa.Column("buoiTrongNgay", sa.String(50), nullable=True),
        _bool_false("laNgayRam"),
        _ngay_tao("thoiDiem"),
    )
    op.create_table(
        "GoiY",
        _pk("idGoiY"),
        _fk("idNguCanh", "NguCanh.idNguCanh", "fk_goiy_nguccanh"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_goiy_nguoidung"),
        _fk("idMonAn", "MonAn.idMonAn", "fk_goiy_monan", ondelete="SET NULL", nullable=True),
        _fk("idDiaDiem", "DiaDiem.idDiaDiem", "fk_goiy_diadiem", ondelete="SET NULL", nullable=True),
        sa.Column("loaiGoiY", sa.String(30), nullable=False),
        sa.Column("diemSo", sa.Numeric(6, 4), nullable=True),
        sa.Column("thuHang", sa.Integer(), nullable=True),
        sa.Column("lyDoGiaiThich", sa.Text(), nullable=True),
        _ngay_tao(),
    )
    op.create_table(
        "CuocTroChuyen",
        _pk("idCuocTroChuyen"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_ctc_nguoidung"),
        sa.Column("tieuDe", sa.String(255), nullable=True),
        _ngay_tao(),
    )
    op.create_table(
        "TinNhan",
        _pk("idTinNhan"),
        _fk("idCuocTroChuyen", "CuocTroChuyen.idCuocTroChuyen", "fk_tn_cuoctro"),
        _fk("idGoiY", "GoiY.idGoiY", "fk_tn_goiy", ondelete="SET NULL", nullable=True),
        sa.Column("nguoiGui", sa.String(30), nullable=False),
        sa.Column("noiDung", sa.Text(), nullable=False),
        _ngay_tao(),
        sa.Column("loaiNoiDung", sa.String(30), nullable=False, server_default=sa.text("'text'")),
    )
    op.create_table(
        "DanhGia",
        _pk("idDanhGia"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_dg_nguoidung"),
        _fk("idDiaDiem", "DiaDiem.idDiaDiem", "fk_dg_diadiem", nullable=True),
        _fk("idMonAn", "MonAn.idMonAn", "fk_dg_monan", nullable=True),
        sa.Column("nguon", sa.String(50), nullable=True),
        sa.Column("diemSo", sa.Integer(), nullable=False),
        sa.Column("noiDung", sa.Text(), nullable=True),
        sa.Column("trangThai", sa.String(30), nullable=False),
        _ngay_tao(),
        sa.CheckConstraint("diemSo between 1 and 5", name="chk_dg_diem"),
    )
    op.create_table(
        "DanhSachYeuThich",
        _pk("idDanhSachYeuThich"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_yt_nguoidung"),
        _fk("idMonAn", "MonAn.idMonAn", "fk_yt_monan", nullable=True),
        _fk("idDiaDiem", "DiaDiem.idDiaDiem", "fk_yt_diadiem", nullable=True),
        _ngay_tao(),
    )
    op.create_table(
        "LichSuScan",
        _pk("idLichSuScan"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_scan_nguoidung"),
        _fk("idMonAn", "MonAn.idMonAn", "fk_scan_monan", ondelete="SET NULL", nullable=True),
        sa.Column("duongDanAnh", sa.Text(), nullable=False),
        sa.Column("doTinCay", sa.Numeric(5, 4), nullable=True),
        sa.Column("ketQuaTho", sa.Text(), nullable=True),
        _ngay_tao(),
    )
    op.create_table(
        "BaoCao",
        _pk("idBaoCao"),
        _fk("idNguoiDung", "NguoiDung.idNguoiDung", "fk_bc_nguoidung"),
        _fk("idDiaDiem", "DiaDiem.idDiaDiem", "fk_bc_diadiem"),
        sa.Column("lyDo", sa.String(255), nullable=False),
        sa.Column("moTa", sa.Text(), nullable=True),
        sa.Column("trangThai", sa.String(30), nullable=False),
        sa.Column("ketQuaXuLy", sa.Text(), nullable=True),
        sa.Column("xuLyLuc", sa.DateTime(), nullable=True),
        _ngay_tao(),
    )
    op.create_table(
        "ChiTietBaoCao",
        _pk("idChiTietBaoCao"),
        _fk("idBaoCao", "BaoCao.idBaoCao", "fk_ctbc_baocao"),
        _fk("idMonAn", "MonAn.idMonAn", "fk_ctbc_monan"),
        sa.Column("ketQuaXuLy", sa.String(255), nullable=True),
        sa.UniqueConstraint("idBaoCao", "idMonAn", name="uq_ctbc"),
    )


def downgrade() -> None:
    for table in (
        "ChiTietBaoCao",
        "BaoCao",
        "LichSuScan",
        "DanhSachYeuThich",
        "DanhGia",
        "TinNhan",
        "CuocTroChuyen",
        "GoiY",
        "NguCanh",
        "NhuCauTheoNgay",
        "SoThichNguoiDung",
        "MonAnSoThich",
        "SoThich",
        "CheDoAnNguoiDung",
        "MonAnCheDoAn",
        "CheDoAn",
        "MonAnDiaDiem",
        "DiaDiem",
        "MonAnNguyenLieu",
        "NguyenLieu",
        "MonAn",
        "DanhMucMonAn",
        "TokenDatLaiMatKhau",
        "NguoiDung",
    ):
        op.drop_table(table)
