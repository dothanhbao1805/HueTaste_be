import uuid

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class CheDoAn(Base):
    __tablename__ = "CheDoAn"
    __table_args__ = (UniqueConstraint("tenCheDo", name="uq_chedoan_ten"),)

    idCheDoAn: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    tenCheDo: Mapped[str] = mapped_column(String(150), nullable=False)
    moTa: Mapped[str | None] = mapped_column(Text, nullable=True)
