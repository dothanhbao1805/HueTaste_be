# Kiến trúc

```
be/
├─ app/
│  ├─ main.py            # FastAPI app, CORS, exception handler, include router /api/v1, /health
│  ├─ core/              # config (pydantic-settings/.env), security (bcrypt, JWT, reset token),
│  │                     # exceptions (AppException...), constants (enum VaiTro, TrangThaiNguoiDung)
│  ├─ db/                # base.py (Base), session.py (engine, SessionLocal, get_db)
│  ├─ models/            # SQLAlchemy models, đăng ký trong models/__init__.py
│  ├─ schemas/           # Pydantic request/response (+ common.Page, common.Message)
│  ├─ repositories/      # Truy vấn DB thuần
│  ├─ services/          # Nghiệp vụ (+ email_service)
│  └─ api/
│     ├─ deps.py         # DbSession, CurrentUser, CurrentAdmin (get_current_user, require_admin)
│     └─ v1/router.py    # gom router; endpoints/{auth,users,admin_users}.py
├─ alembic/              # migrations (env.py đọc DATABASE_URL từ app.core.config)
├─ scripts/create_admin.py
├─ tests/                # pytest, SQLite in-memory, override get_db
└─ claude/               # rules này
```

## Luồng và trách nhiệm
`endpoint → service → repository → model`

| Tầng | Được làm | Không được |
|---|---|---|
| endpoint | khai báo route, validate qua schema, gọi service, trả response | logic nghiệp vụ, query DB |
| service | quy tắc nghiệp vụ, ném `AppException`, **`db.commit()`**, gọi email/dịch vụ ngoài | import FastAPI/Request |
| repository | câu truy vấn SQLAlchemy, `add` + `flush` | `commit`, quy tắc nghiệp vụ |
| schema | định nghĩa & validate dữ liệu vào/ra | truy cập DB |

Phân quyền: dùng dependency `CurrentUser` / `CurrentAdmin` trong `app/api/deps.py` (router admin gắn `dependencies=[Depends(require_admin)]`). Token JWT có claim `type` = `access`|`refresh`; user `blocked` bị chặn ở cả login và mỗi request.

DB session: một `Session` mỗi request qua `get_db`; sync SQLAlchemy (không async).
