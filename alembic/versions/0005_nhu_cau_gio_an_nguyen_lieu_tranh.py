"""NhuCauTheoNgay: giờ ăn của bữa + nguyên liệu cần tránh (CSV idNguyenLieu)

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("NhuCauTheoNgay") as batch:
        batch.add_column(sa.Column("gioAn", sa.Time(), nullable=True))
        batch.add_column(sa.Column("nguyenLieuTranh", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("NhuCauTheoNgay") as batch:
        batch.drop_column("nguyenLieuTranh")
        batch.drop_column("gioAn")
