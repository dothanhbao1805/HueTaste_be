# Backend – Hệ thống gợi ý món ăn theo ngữ cảnh (TP Huế)

FastAPI + MySQL + SQLAlchemy 2.0 + Alembic. Client: app Android (Kotlin) cho user, ReactJS cho Admin.

**Trước khi sửa code, đọc các rules trong thư mục [`claude/`](claude/README.md)** (kiến trúc, quy ước, cách thêm tính năng).

Quy tắc cốt lõi:
- Luồng: `endpoint -> service -> repository -> model`. Endpoint mỏng, service chứa nghiệp vụ và `commit`, repository chỉ truy vấn (`flush`, không `commit`).
- Tên bảng/cột giữ đúng tài liệu đồ án (vd `NguoiDung.matKhauMaHoa`); tên file/hàm Python dùng snake_case.
- Thay đổi schema DB => luôn tạo Alembic migration (viết tay, xem 04-...md); thêm model => import vào `app/models/__init__.py`.
- Lỗi nghiệp vụ ném `AppException` (app/core/exceptions.py), trả JSON `{code, message}`.
- Mỗi tính năng mới phải có test trong `tests/`; chạy `.venv\Scripts\python -m pytest`.
- DB `huetaste` có đủ 24 bảng và đã có model (xem `claude/04-database-and-migrations.md`); PK dạng `id<TênBảng>` kiểu `UUIDChar36`.
- Dữ liệu món/quán do pipeline tự động (LLM: liệt kê món Gemini → Groq, trích tag Groq → Gemini; + Wikipedia + Serper, worker `scripts/worker.py`) và gợi ý `POST /goi-y`: xem `claude/08-pipeline-va-goi-y.md`.
- Nhiều ảnh cho món/quán: pipeline gọi Serper Images lưu vào `AnhMonAn`/`AnhDiaDiem` (`thu_thap_service._luu_anh_mon/_luu_anh_quan`), chi tiết trong `claude/08-pipeline-va-goi-y.md`.
- Dịch vụ ngoài gọi qua `app/services/*_service.py` (httpx), test luôn mock bằng `monkeypatch`, không gọi mạng thật.
- Ảnh upload lưu ở `UPLOAD_DIR` qua `luu_tru_service.luu_anh`, phục vụ tại `/uploads/...`.
- Báo cáo: món `VI_PHAM` bị gỡ khỏi quán (xóa `MonAnDiaDiem`), pipeline kiểm tra `bao_cao_repo.mon_bi_go` để không gắn lại; admin có thể ẩn quán.
- Scan ảnh `POST /scan` (`scan_service`, model vision `GEMINI_MODEL_SCAN`): món Huế chưa có -> tạo `unverified` + `thu_thap_service.lam_giau_mon` chạy nền; xem `claude/08-pipeline-va-goi-y.md`.
- Chưa làm: chatbot, đổi ngôn ngữ.
