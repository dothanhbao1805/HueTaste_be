import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class MonAnCheDoAn(Base):
    __tablename__ = "MonAnCheDoAn"
    __table_args__ = (UniqueConstraint("idMonAn", "idCheDoAn", name="uq_monan_chedoan"),)

    idMonAnCheDoAn: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idMonAn: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_macd_monan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idCheDoAn: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("CheDoAn.idCheDoAn", name="fk_macd_chedoan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
