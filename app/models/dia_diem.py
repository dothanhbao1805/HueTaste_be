import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import TIMESTAMP, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class DiaDiem(Base):
    __tablename__ = "DiaDiem"
    __table_args__ = (UniqueConstraint("maGooglePlace", name="uq_diadiem_googleplace"),)

    idDiaDiem: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    maGooglePlace: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenDiaDiem: Mapped[str] = mapped_column(String(255), nullable=False)
    diaChi: Mapped[str | None] = mapped_column(Text, nullable=True)
    viDo: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    kinhDo: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    soDienThoai: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gioMoCua: Mapped[str | None] = mapped_column(Text, nullable=True)
    mucGia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # diemTrungBinh = gộp rating Google (2 cột dưới, migration 0003) với đánh giá trong app
    diemTrungBinh: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    diemGoogle: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    soDanhGiaGoogle: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hinhAnh: Mapped[str | None] = mapped_column(Text, nullable=True)
    trangThai: Mapped[str] = mapped_column(String(30), nullable=False)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    ngayCapNhat: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )
