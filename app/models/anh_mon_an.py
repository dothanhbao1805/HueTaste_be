import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class AnhMonAn(Base):
    """Ảnh phụ của món (Serper Images). Ảnh bìa vẫn là MonAn.hinhAnh. urlHash = sha256(url) để chống trùng."""

    __tablename__ = "AnhMonAn"
    __table_args__ = (UniqueConstraint("idMonAn", "urlHash", name="uq_anhmonan_url"),)

    idAnhMonAn: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idMonAn: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_anhmonan_monan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    urlHash: Mapped[str] = mapped_column(String(64), nullable=False)
    urlThumbnail: Mapped[str | None] = mapped_column(Text, nullable=True)
    nguon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thuTu: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
