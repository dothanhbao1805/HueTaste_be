# Chạy & test (Windows, PowerShell)

```powershell
# cài đặt lần đầu
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env          # sửa DATABASE_URL, SECRET_KEY

# tạo DB trong MySQL: CREATE DATABASE huetaste CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# tạo/cập nhật bảng. DB huetaste tạo tay đã được `alembic stamp 0001`; upgrade head sẽ áp 0002 (chống trùng)
.venv\Scripts\python -m alembic upgrade head

# tạo admin đầu tiên
.venv\Scripts\python -m scripts.create_admin --email admin@example.com --password 12345678 --name "Admin"

# điền GROQ_API_KEY (console.groq.com; GEMINI_API_KEY dự phòng, tuỳ chọn) và SERPER_API_KEY (serper.dev) trong .env, rồi nạp dữ liệu lần đầu
.venv\Scripts\python -m scripts.thu_thap_du_lieu --mon-an --so-mon 20
.venv\Scripts\python -m scripts.thu_thap_du_lieu --dia-diem

# worker chạy định kỳ (cửa sổ riêng, để chạy nền)
.venv\Scripts\python -m scripts.worker

# chạy server (docs: http://localhost:8000/docs)
.venv\Scripts\python -m uvicorn app.main:app --reload

# test
.venv\Scripts\python -m pytest
```

- Test dùng SQLite in-memory (`tests/conftest.py`), không cần MySQL; `get_db` được override.
- Chưa cấu hình `SMTP_HOST` thì email reset mật khẩu chỉ được log ra console (tìm `[DEV EMAIL]`) – lấy token ở đó để thử `/auth/reset-password`.
- Test chạy trên SQLite nên không bắt được lỗi riêng của MySQL; sau khi sửa model/migration hãy chạy thử `alembic upgrade head` trên MySQL thật.
