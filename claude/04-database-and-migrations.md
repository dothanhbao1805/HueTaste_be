# Database & migrations

DB: MySQL 8, database **`huetaste`** (driver PyMySQL, URL `mysql+pymysql://user:pass@localhost:3306/huetaste?charset=utf8mb4`). Schema được tạo tay trong MySQL trước; models + migration `0001` mô tả lại đúng schema đó.

## Bảng hiện có (24 bảng đồ án + `AnhMonAn`, `AnhDiaDiem` từ migration 0004, khớp MySQL `huetaste`)
| Nhóm | Model (file trong `app/models/`) |
|---|---|
| Người dùng | `NguoiDung` (nguoi_dung), `TokenDatLaiMatKhau` (token_dat_lai_mat_khau) |
| Món ăn | `DanhMucMonAn`, `MonAn`, `NguyenLieu`, `MonAnNguyenLieu` |
| Địa điểm | `DiaDiem`, `MonAnDiaDiem` |
| Chế độ ăn | `CheDoAn`, `MonAnCheDoAn`, `CheDoAnNguoiDung` |
| Sở thích | `SoThich`, `MonAnSoThich`, `SoThichNguoiDung` (`mucDo` 1–5) |
| Ngữ cảnh/gợi ý | `NhuCauTheoNgay`, `NguCanh`, `GoiY` |
| Tương tác | `DanhGia` (`diemSo` 1–5), `DanhSachYeuThich`, `LichSuScan` |
| Chatbot | `CuocTroChuyen`, `TinNhan` |
| Báo cáo | `BaoCao`, `ChiTietBaoCao` |

Migration `0002`: thêm `MonAn.tenChuanHoa` (UNIQUE, khoá so trùng = `chuan_hoa_ten(tenMon)`), `MonAn.maWikipedia` (UNIQUE, pageid), `MonAn.nguonThamKhao` (URL nguồn); unique tên cho `DanhMucMonAn`, `NguyenLieu`, `SoThich(loai, tenSoThich)`, `CheDoAn`. Collation `utf8mb4_unicode_ci` nên unique tên không phân biệt hoa/thường.

Migration `0003`: unique `(idNguoiDung, idMonAn)` và `(idNguoiDung, idDiaDiem)` cho `DanhSachYeuThich` và `DanhGia` (mỗi người 1 lượt yêu thích/1 đánh giá cho mỗi món/quán); `DiaDiem.diemGoogle`, `DiaDiem.soDanhGiaGoogle` (rating Google do pipeline ghi). `DiaDiem.diemTrungBinh` = TB có trọng số của rating Google và đánh giá app (`danh_gia_service.tinh_lai_diem_quan`). "Đúng 1 trong idMonAn/idDiaDiem" kiểm tra ở schema (`schemas/yeu_thich.DoiTuong`) vì MySQL cấm CHECK trên cột có FK `ON DELETE CASCADE`.

Migration `0004`: bảng `AnhMonAn`, `AnhDiaDiem` (nhiều ảnh phụ cho món/quán từ Serper Images): `url`, `urlHash` (sha256, unique cùng id cha để chống trùng), `urlThumbnail`, `nguon`, `thuTu`; FK `ON DELETE CASCADE`. Ảnh bìa vẫn ở `MonAn.hinhAnh` / `DiaDiem.hinhAnh`.

Migration `0005`: `NhuCauTheoNgay.gioAn` (TIME, giờ dự định ăn bữa đó), `NhuCauTheoNgay.nguyenLieuTranh` (TEXT, CSV `idNguyenLieu` cần tránh; `nhu_cau_repo.ghep_ids/tach_ids`). Không thêm bảng: lọc món bằng `MonAnNguyenLieu`.

Chú ý:
- PK tên `id<TênBảng>` (vd `NguoiDung.idNguoiDung`), kiểu `UUIDChar36` (`app/db/types.py`) = CHAR(36) **có gạch nối**, khớp `DEFAULT (uuid())` của MySQL. Không dùng `sqlalchemy.Uuid` (lưu CHAR(32) không gạch nối → lệch với bản ghi MySQL tự sinh).
- `maToken` lưu hash SHA-256, không phải token gốc.
- `vaiTro` ∈ {`user`,`admin`}, `trangThai` (NguoiDung) ∈ {`active`,`blocked`}.
- `trangThai` (MonAn/DiaDiem) ∈ {`active`,`hidden`,`unverified`} (`TrangThaiNoiDung`); API chỉ trả `active`.
- `MonAn.buoiPhuHop`/`thoiTietPhuHop` lưu CSV giá trị enum `Buoi`/`ThoiTiet` (vd `sang,trua`). `SoThich.loai` ∈ {`vi`,`kieu`}, `tenSoThich` lấy từ `VI_MON`/`KIEU_MON`. `GoiY.loaiGoiY` ∈ {`mon_an`,`dia_diem`}.
- Cột `ngayTao/ngayCapNhat/thoiDiem` là `TIMESTAMP`; `hetHanLuc`, `xuLyLuc` là `DATETIME`. MySQL trả datetime naive — code luôn dùng UTC và gắn `tzinfo` khi so sánh.
- Tên FK/unique/check đặt đúng tên constraint trong DB (`fk_...`, `uq_...`, `chk_...`). FK không khai báo `index=True` vì MySQL tự tạo index theo tên FK.

## Quy trình đổi schema
1. Sửa/tạo model trong `app/models/`, **import vào `app/models/__init__.py`**.
2. Viết migration mới `alembic/versions/000N_<mo_ta>.py` (`down_revision` = bản trước). **Không tin autogenerate trên Windows**: MySQL `lower_case_table_names=1` trả tên bảng chữ thường nên autogenerate sẽ đề xuất drop/create toàn bộ bảng — nếu dùng thì xóa hết phần thừa.
3. Áp dụng: `.venv\Scripts\python -m alembic upgrade head`.
4. Không sửa migration đã áp dụng; tạo migration mới.

DB `huetaste` đã có bảng sẵn (tạo tay) → chạy **một lần** `.venv\Scripts\python -m alembic stamp 0001` để Alembic ghi nhận, sau đó mới `upgrade` các migration tiếp theo. DB trống → `upgrade head` tạo đủ 24 bảng.

## Lưu ý camelCase
Tên cột camelCase: SQL viết tay nên đặt trong dấu backtick (`` SELECT `matKhauMaHoa` FROM `NguoiDung` ``). Trên Windows tên bảng thực tế là chữ thường (`nguoidung`); ORM vẫn dùng `NguoiDung` và chạy được. Nếu chuyển DB sang Linux (`lower_case_table_names=0`) phải giữ cấu hình này hoặc đổi `__tablename__`.

## Quy ước khi thêm bảng
- PK `id<TênBảng>: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)`.
- FK đặt tên cột `id<TênBảngNguồn>`; `ForeignKey("Bang.idBang", name="fk_...", ondelete=..., onupdate="CASCADE")`.
- `ngayTao` = `TIMESTAMP, server_default=func.now()`; `ngayCapNhat` thêm `onupdate=func.now()` (migration MySQL: `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`).
- Cột cho phép NULL → `Mapped[X | None]`, `nullable=True`. Decimal → `Numeric(p, s)` (vĩ độ/kinh độ `Numeric(10, 7)`).
