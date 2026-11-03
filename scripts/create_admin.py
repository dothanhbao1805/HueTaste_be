"""Tạo tài khoản admin đầu tiên.

Chạy từ thư mục be/:  python -m scripts.create_admin --email admin@example.com --password 12345678 --name "Admin"
"""
import argparse

from app.core import security
from app.core.constants import TrangThaiNguoiDung, VaiTro
from app.db.session import SessionLocal
from app.repositories import nguoi_dung_repo


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Administrator")
    args = parser.parse_args()

    with SessionLocal() as db:
        if nguoi_dung_repo.get_by_email(db, args.email):
            print("Email đã tồn tại, bỏ qua.")
            return
        nguoi_dung_repo.create(
            db,
            email=args.email.lower(),
            matKhauMaHoa=security.hash_password(args.password),
            hoTen=args.name,
            vaiTro=VaiTro.ADMIN.value,
            trangThai=TrangThaiNguoiDung.ACTIVE.value,
        )
        db.commit()
        print(f"Đã tạo admin: {args.email}")


if __name__ == "__main__":
    main()
