import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import TIMESTAMP, Date, ForeignKey, Numeric, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class NhuCauTheoNgay(Base):
    __tablename__ = "NhuCauTheoNgay"

    idNhuCauTheoNgay: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36, primary_key=True, default=uuid.uuid4
    )
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_nc_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    ngay: Mapped[date] = mapped_column(Date, nullable=False)
    buaAn: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nganSach: Mapped[Decimal | None] = mapped_column(Numeric(12, 0), nullable=True)
    ghiChu: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gioAn: Mapped[time | None] = mapped_column(Time, nullable=True)
    nguyenLieuTranh: Mapped[str | None] = mapped_column(Text, nullable=True)  # CSV idNguyenLieu
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    ngayCapNhat: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )
