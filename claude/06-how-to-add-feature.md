# Checklist thêm tính năng mới

Ví dụ: thêm bảng `DanhMucMonAn` + CRUD cho admin.

1. **Tra tài liệu** `Cac_chuc_nang_cua_tac_nhan.docx` để lấy đúng tên cột/kiểu/ràng buộc.
2. **Model** – `app/models/danh_muc_mon_an.py` (mẫu: `nguoi_dung.py`), rồi thêm import vào `app/models/__init__.py`.
3. **Migration** – autogenerate, kiểm tra tay, `upgrade head` (xem `04-database-and-migrations.md`).
4. **Schema** – `app/schemas/danh_muc_mon_an.py`: `DanhMucOut` (`from_attributes=True`), `TaoDanhMuc`, `CapNhatDanhMuc`. Dùng `Page[T]` cho danh sách.
5. **Repository** – `app/repositories/danh_muc_repo.py`: hàm nhận `db: Session`, chỉ truy vấn + `flush` (mẫu: `nguoi_dung_repo.py`).
6. **Service** – `app/services/danh_muc_service.py`: kiểm tra nghiệp vụ, ném `NotFoundError/ConflictError`, **`db.commit()`** (mẫu: `nguoi_dung_service.py`).
7. **Endpoint** – `app/api/v1/endpoints/admin_danh_muc.py` với `APIRouter(prefix="/admin/danh-muc", dependencies=[Depends(require_admin)])`; đăng ký vào `app/api/v1/router.py`.
8. **Test** – `tests/test_danh_muc.py` dùng fixtures `client`, `admin_user`, `auth_header` trong `tests/conftest.py`: happy path + 401/403 + trùng/không thấy.
9. **Chạy** `.venv\Scripts\python -m pytest`, cập nhật bảng endpoint ở `05-api-guidelines.md`, mục "đã làm" ở `01-project-overview.md` và bảng bảng DB ở `04-...md`.

## Khi cần dịch vụ ngoài (email, Serper, thời tiết, LLM qua llm_service...)
Đặt trong `app/services/<ten>_service.py` với hàm thuần dễ mock (xem `email_service.py`); cấu hình qua `settings`; trong test dùng `monkeypatch` để thay thế (xem `test_forgot_and_reset_password`).

## Upload ảnh (chụp/tải ảnh món ăn – sau này)
Dùng `python-multipart` (đã cài) và `UploadFile`; lưu file qua một service lưu trữ riêng, DB chỉ giữ đường dẫn (`duongDanAnh`).
