# Quy ước code

## Đặt tên
- **Bảng và cột DB giữ đúng tài liệu đồ án**: `__tablename__ = "NguoiDung"`, cột `matKhauMaHoa`, `ngayTao`... (camelCase, tiếng Việt không dấu). Thuộc tính model Python trùng tên cột.
- **Field trong schema/JSON cũng camelCase giống cột** (`hoTen`, `matKhau`, `accessToken`) để app Kotlin/React ánh xạ thẳng.
- File, module, hàm, biến cục bộ, tham số hàm Python: `snake_case` (vd `nguoi_dung_repo.py`, `ho_ten`). Class: `PascalCase`.
- Tên file model = snake_case của tên bảng (`token_dat_lai_mat_khau.py`).
- Schema đặt tên tiếng Việt theo hành động: `DangKy`, `DangNhap`, `CapNhatThongTin`; output: `<Bang>Out`.
- Giá trị enum lưu trong DB là chuỗi thường: `user`/`admin`, `active`/`blocked`; định nghĩa ở `app/core/constants.py` (`StrEnum`).

## Quy tắc
- Có type hints đầy đủ; Python 3.13 (`X | None`, không dùng `Optional`).
- Lỗi nghiệp vụ: ném `AppException` hoặc lớp con (`NotFoundError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`) với `code` viết HOA_GẠCH_DƯỚI ổn định (client dựa vào `code`). Thông báo `message` tiếng Việt.
- Không bao giờ log/trả về `matKhauMaHoa`; schema output không có field này.
- Mật khẩu: bcrypt (`security.hash_password`). Token đặt lại mật khẩu: lưu **hash SHA-256** vào `maToken`, gửi bản gốc qua email.
- Email chuẩn hóa `lower()` trước khi lưu/tra cứu.
- `forgot-password` luôn trả 200 dù email không tồn tại (chống dò email).
- Thời gian: `DateTime(timezone=True)`, tạo bằng `datetime.now(timezone.utc)`; cột `ngayTao/ngayCapNhat` dùng `server_default=func.now()`.
- Cấu hình/bí mật chỉ qua `.env` → `app.core.config.settings`; không hard-code.
- Comment ngắn, chỉ giải thích "tại sao"; code và docstring tiếng Việt hoặc Anh đều được nhưng nhất quán với file xung quanh.
