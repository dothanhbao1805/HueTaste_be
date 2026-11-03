# Tổng quan dự án

**Đề tài:** Xây dựng hệ thống gợi ý món ăn dựa trên ngữ cảnh người dùng tại thành phố Huế.

**Thành phần:** App Android (Kotlin) cho người dùng · Web ReactJS cho Admin · Backend (repo này) FastAPI.

**Tài liệu gốc:** `E:\Đồ án tốt nghiệp\Cac_chuc_nang_cua_tac_nhan.docx` (chức năng từng tác nhân + thiết kế bảng), `ERD.mdj`, `Actor_UseCase_...docx`.

## Tác nhân
- **Admin:** đăng nhập, quản lý người dùng, cập nhật danh mục món ăn, xem thống kê, xử lý nội dung bị báo cáo.
- **Người dùng:** đăng ký/đăng nhập, đặt lại mật khẩu, cập nhật hồ sơ, chụp/tải ảnh món ăn, sở thích & chế độ ăn, nhu cầu theo ngày, xem gợi ý món/địa điểm theo ngữ cảnh, chat trợ lý ảo, báo cáo, tìm kiếm, xem chi tiết, đánh giá, bản đồ, yêu thích, đổi ngôn ngữ.
- **Trợ lý ảo:** tư vấn/gợi ý, giải thích lý do, trả lời câu hỏi, nhận diện món ăn.

## Trạng thái hiện tại
Models: đủ 24 bảng DB `huetaste` (+ migration 0002 chống trùng). Đã làm:
- Auth: đăng ký, đăng nhập user/admin, refresh token, quên/đặt lại mật khẩu; hồ sơ, đổi mật khẩu.
- Admin: quản lý người dùng (tìm, lọc, phân trang, khóa/mở); kích hoạt thu thập dữ liệu.
- Pipeline dữ liệu tự động (LLM Groq/Gemini → Wikipedia → Serper) + worker định kỳ, chống trùng 4 lớp.
- Tra cứu: danh mục, món ăn (tên không dấu, nguyên liệu, chi tiết), địa điểm (theo khoảng cách, chi tiết).
- Sở thích & chế độ ăn của người dùng.
- Gợi ý món + quán theo ngữ cảnh (giờ, thời tiết, âm lịch, vị trí, ngân sách, ghi chú) có lý do giải thích.
- Admin CRUD danh mục món ăn (pipeline xếp món theo danh mục trong DB). Món/quán chỉ do pipeline tạo, admin không sửa.
- Nhu cầu theo ngày (`/users/me/nhu-cau`), `/goi-y` tự dùng ngân sách/ghi chú/nguyên liệu cần tránh đã lưu cho bữa đó và chọn bữa theo giờ ăn đã đặt.
- Upload ảnh (`/uploads`, `/users/me/avatar`).
- Scan ảnh nhận diện món (`/scan`, Gemini vision): món Huế chưa có được tự thêm và tìm hiểu nền, món khác chỉ trả thông tin cơ bản.
- Yêu thích món/quán, đánh giá món/quán (điểm quán gộp rating Google + app).
- Báo cáo quán (kèm món sai), admin duyệt từng món: `VI_PHAM` gỡ món khỏi quán (pipeline không gắn lại), có thể ẩn quán.
- Thống kê admin: tổng quan, lượt gợi ý theo ngày, top món được gợi ý.

**Chưa làm:** chatbot (CuocTroChuyen, TinNhan), đổi ngôn ngữ.
