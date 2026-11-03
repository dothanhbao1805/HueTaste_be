import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class AnhDiaDiem(Base):
    """Ảnh phụ của quán (Serper Images + thumbnail Maps). Ảnh bìa vẫn là DiaDiem.hinhAnh."""

    __tablename__ = "AnhDiaDiem"
    __table_args__ = (UniqueConstraint("idDiaDiem", "urlHash", name="uq_anhdiadiem_url"),)

    idAnhDiaDiem: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idDiaDiem: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("DiaDiem.idDiaDiem", name="fk_anhdiadiem_diadiem", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    urlHash: Mapped[str] = mapped_column(String(64), nullable=False)
    urlThumbnail: Mapped[str | None] = mapped_column(Text, nullable=True)
    nguon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thuTu: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
