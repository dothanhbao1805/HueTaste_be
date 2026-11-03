"""Xoá TOÀN BỘ dữ liệu trong các bảng (TRUNCATE), giữ nguyên cấu trúc bảng và alembic_version.

Chạy từ thư mục be/:  python -m scripts.xoa_du_lieu
Dừng server và worker trước khi chạy. Không thể hoàn tác - nên mysqldump sao lưu trước.
"""
from sqlalchemy import text

import app.models  # noqa: F401  đăng ký đủ 24 bảng vào metadata
from app.db.base import Base
from app.db.session import engine


def main() -> None:
    db_name = engine.url.database
    bang = [t.name for t in Base.metadata.sorted_tables]
    print(f"Sẽ xoá toàn bộ dữ liệu của {len(bang)} bảng trong database '{db_name}' (giữ cấu trúc bảng).")
    if input("Gõ XOA để xác nhận: ").strip() != "XOA":
        print("Đã huỷ, không xoá gì.")
        return

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        try:
            for ten in reversed(bang):
                conn.execute(text(f"TRUNCATE TABLE `{ten}`"))
        finally:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    print(f"Đã xoá dữ liệu {len(bang)} bảng. Nhớ tạo lại admin: python -m scripts.create_admin ...")


if __name__ == "__main__":
    main()
