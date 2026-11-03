import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class MonAnSoThich(Base):
    __tablename__ = "MonAnSoThich"
    __table_args__ = (UniqueConstraint("idMonAn", "idSoThich", name="uq_monan_sothich"),)

    idMonAnSoThich: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idMonAn: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_mast_monan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idSoThich: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("SoThich.idSoThich", name="fk_mast_sothich", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    trongSo: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("1.00"), server_default=text("1.00")
    )
