"""DanhSachYeuThich/DanhGia: chống trùng; DiaDiem: tách rating Google để gộp với đánh giá app

"Đúng 1 trong idMonAn/idDiaDiem" kiểm tra ở schema: MySQL cấm CHECK trên cột có FK ON DELETE CASCADE.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (bảng, tiền tố tên constraint)
_BANG = (("DanhSachYeuThich", "yt"), ("DanhGia", "dg"))


def upgrade() -> None:
    for table, tt in _BANG:
        with op.batch_alter_table(table) as batch:
            batch.create_unique_constraint(f"uq_{tt}_nguoidung_monan", ["idNguoiDung", "idMonAn"])
            batch.create_unique_constraint(f"uq_{tt}_nguoidung_diadiem", ["idNguoiDung", "idDiaDiem"])
    with op.batch_alter_table("DiaDiem") as batch:
        batch.add_column(sa.Column("diemGoogle", sa.Numeric(3, 2), nullable=True))
        batch.add_column(sa.Column("soDanhGiaGoogle", sa.Integer(), nullable=True))
    # trước migration này diemTrungBinh chính là rating Google
    dia_diem = sa.table("DiaDiem", sa.column("diemGoogle"), sa.column("diemTrungBinh"))
    op.execute(dia_diem.update().values(diemGoogle=dia_diem.c.diemTrungBinh))


def downgrade() -> None:
    with op.batch_alter_table("DiaDiem") as batch:
        batch.drop_column("soDanhGiaGoogle")
        batch.drop_column("diemGoogle")
    for table, tt in reversed(_BANG):
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(f"uq_{tt}_nguoidung_diadiem", type_="unique")
            batch.drop_constraint(f"uq_{tt}_nguoidung_monan", type_="unique")
