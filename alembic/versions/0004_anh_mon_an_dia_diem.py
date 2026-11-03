"""AnhMonAn, AnhDiaDiem: nhiều ảnh cho món/quán (Serper Images)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-31
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.types import UUIDChar36

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (bảng, cột PK, cột FK, bảng cha, cột PK bảng cha, tên FK, tên unique)
_BANG = (
    ("AnhMonAn", "idAnhMonAn", "idMonAn", "MonAn", "fk_anhmonan_monan", "uq_anhmonan_url"),
    ("AnhDiaDiem", "idAnhDiaDiem", "idDiaDiem", "DiaDiem", "fk_anhdiadiem_diadiem", "uq_anhdiadiem_url"),
)


def upgrade() -> None:
    mysql = op.get_bind().dialect.name == "mysql"
    for bang, pk, fk, cha, fk_name, uq_name in _BANG:
        op.create_table(
            bang,
            sa.Column(
                pk, UUIDChar36(), primary_key=True, server_default=sa.text("(uuid())") if mysql else None
            ),
            sa.Column(
                fk,
                UUIDChar36(),
                sa.ForeignKey(f"{cha}.{fk}", name=fk_name, ondelete="CASCADE", onupdate="CASCADE"),
                nullable=False,
            ),
            sa.Column("url", sa.Text(), nullable=False),
            sa.Column("urlHash", sa.String(64), nullable=False),
            sa.Column("urlThumbnail", sa.Text(), nullable=True),
            sa.Column("nguon", sa.String(255), nullable=True),
            sa.Column("thuTu", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("ngayTao", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint(fk, "urlHash", name=uq_name),
        )


def downgrade() -> None:
    for bang, *_ in reversed(_BANG):
        op.drop_table(bang)
