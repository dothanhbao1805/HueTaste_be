# Rules cho Claude – Backend

Đọc theo thứ tự khi bắt đầu một phiên làm việc mới:

1. [01-project-overview.md](01-project-overview.md) – đề tài, actor, phạm vi đã/chưa làm, roadmap.
2. [02-architecture.md](02-architecture.md) – cấu trúc thư mục, luồng layer, trách nhiệm từng tầng.
3. [03-coding-conventions.md](03-coding-conventions.md) – quy ước đặt tên, lỗi, bảo mật.
4. [04-database-and-migrations.md](04-database-and-migrations.md) – model, Alembic, đối chiếu tài liệu ↔ model.
5. [05-api-guidelines.md](05-api-guidelines.md) – URL, auth, format response/lỗi, phân trang, danh sách endpoint hiện có.
6. [06-how-to-add-feature.md](06-how-to-add-feature.md) – checklist thêm tính năng (có ví dụ).
7. [07-testing-and-running.md](07-testing-and-running.md) – cài đặt, chạy, test.
8. [08-pipeline-va-goi-y.md](08-pipeline-va-goi-y.md) – pipeline thu thập dữ liệu, chống trùng, worker, công thức gợi ý.

Khi user yêu cầu tính năng mới: tra tài liệu đồ án (`E:\Đồ án tốt nghiệp\Cac_chuc_nang_cua_tac_nhan.docx`, `ERD.mdj`) để lấy đúng tên bảng/cột, rồi làm theo `06-how-to-add-feature.md`. Cập nhật lại các file rules này nếu thay đổi kiến trúc hoặc thêm module.
