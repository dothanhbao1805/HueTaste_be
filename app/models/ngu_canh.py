import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class NguCanh(Base):
    __tablename__ = "NguCanh"

    idNguCanh: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_nguc_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    idNhuCauTheoNgay: Mapped[uuid.UUID | None] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NhuCauTheoNgay.idNhuCauTheoNgay",
            name="fk_nguc_nhucau",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )
    viDo: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    kinhDo: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    nhietDo: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    thoiTiet: Mapped[str | None] = mapped_column(String(50), nullable=True)
    buoiTrongNgay: Mapped[str | None] = mapped_column(String(50), nullable=True)
    laNgayRam: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    thoiDiem: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
