import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class MonAnDiaDiem(Base):
    __tablename__ = "MonAnDiaDiem"
    __table_args__ = (UniqueConstraint("idMonAn", "idDiaDiem", name="uq_monan_diadiem"),)

    idMonAnDiaDiem: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idMonAn: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_madd_monan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idDiaDiem: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("DiaDiem.idDiaDiem", name="fk_madd_diadiem", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    giaBan: Mapped[Decimal | None] = mapped_column(Numeric(12, 0), nullable=True)
    laMonDacTrung: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
