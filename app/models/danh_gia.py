import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class DanhGia(Base):
    __tablename__ = "DanhGia"
    # mỗi người 1 đánh giá cho mỗi món/quán (migration 0003)
    __table_args__ = (
        CheckConstraint("diemSo between 1 and 5", name="chk_dg_diem"),
        UniqueConstraint("idNguoiDung", "idMonAn", name="uq_dg_nguoidung_monan"),
        UniqueConstraint("idNguoiDung", "idDiaDiem", name="uq_dg_nguoidung_diadiem"),
    )

    idDanhGia: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_dg_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    idDiaDiem: Mapped[uuid.UUID | None] = mapped_column(
        UUIDChar36,
        ForeignKey("DiaDiem.idDiaDiem", name="fk_dg_diadiem", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    idMonAn: Mapped[uuid.UUID | None] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_dg_monan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    nguon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    diemSo: Mapped[int] = mapped_column(Integer, nullable=False)
    noiDung: Mapped[str | None] = mapped_column(Text, nullable=True)
    trangThai: Mapped[str] = mapped_column(String(30), nullable=False)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
