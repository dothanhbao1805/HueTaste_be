"""MonAn: nguonThamKhao, maWikipedia, tenChuanHoa + unique chống trùng cho pipeline thu thập

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (bảng, tên constraint, cột)
_UNIQUES = (
    ("DanhMucMonAn", "uq_danhmuc_ten", ["tenDanhMuc"]),
    ("NguyenLieu", "uq_nguyenlieu_ten", ["tenNguyenLieu"]),
    ("SoThich", "uq_sothich_loai_ten", ["loai", "tenSoThich"]),
    ("CheDoAn", "uq_chedoan_ten", ["tenCheDo"]),
)


def upgrade() -> None:
    # MonAn đang trống khi áp dụng migration này nên thêm cột NOT NULL không cần giá trị mặc định
    with op.batch_alter_table("MonAn") as batch:
        batch.add_column(sa.Column("tenChuanHoa", sa.String(255), nullable=False))
        batch.add_column(sa.Column("maWikipedia", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("nguonThamKhao", sa.Text(), nullable=True))
        batch.create_unique_constraint("uq_monan_tenchuanhoa", ["tenChuanHoa"])
        batch.create_unique_constraint("uq_monan_mawikipedia", ["maWikipedia"])
    for table, name, cols in _UNIQUES:
        with op.batch_alter_table(table) as batch:
            batch.create_unique_constraint(name, cols)


def downgrade() -> None:
    for table, name, _ in reversed(_UNIQUES):
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(name, type_="unique")
    with op.batch_alter_table("MonAn") as batch:
        batch.drop_constraint("uq_monan_mawikipedia", type_="unique")
        batch.drop_constraint("uq_monan_tenchuanhoa", type_="unique")
        batch.drop_column("nguonThamKhao")
        batch.drop_column("maWikipedia")
        batch.drop_column("tenChuanHoa")
