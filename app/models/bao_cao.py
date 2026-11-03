import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class BaoCao(Base):
    __tablename__ = "BaoCao"

    idBaoCao: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_bc_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    idDiaDiem: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("DiaDiem.idDiaDiem", name="fk_bc_diadiem", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    lyDo: Mapped[str] = mapped_column(String(255), nullable=False)
    moTa: Mapped[str | None] = mapped_column(Text, nullable=True)
    trangThai: Mapped[str] = mapped_column(String(30), nullable=False)
    ketQuaXuLy: Mapped[str | None] = mapped_column(Text, nullable=True)
    xuLyLuc: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
