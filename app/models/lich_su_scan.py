import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import TIMESTAMP, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class LichSuScan(Base):
    __tablename__ = "LichSuScan"

    idLichSuScan: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_scan_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    idMonAn: Mapped[uuid.UUID | None] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_scan_monan", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    duongDanAnh: Mapped[str] = mapped_column(Text, nullable=False)
    doTinCay: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    ketQuaTho: Mapped[str | None] = mapped_column(Text, nullable=True)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
