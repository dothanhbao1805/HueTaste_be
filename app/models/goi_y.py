import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class GoiY(Base):
    __tablename__ = "GoiY"

    idGoiY: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idNguCanh: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        # tên "nguccanh" giữ đúng như constraint trong DB
        ForeignKey("NguCanh.idNguCanh", name="fk_goiy_nguccanh", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_goiy_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    idMonAn: Mapped[uuid.UUID | None] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_goiy_monan", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    idDiaDiem: Mapped[uuid.UUID | None] = mapped_column(
        UUIDChar36,
        ForeignKey("DiaDiem.idDiaDiem", name="fk_goiy_diadiem", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    loaiGoiY: Mapped[str] = mapped_column(String(30), nullable=False)
    diemSo: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    thuHang: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lyDoGiaiThich: Mapped[str | None] = mapped_column(Text, nullable=True)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
