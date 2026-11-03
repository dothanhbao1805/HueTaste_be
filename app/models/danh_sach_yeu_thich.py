import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class DanhSachYeuThich(Base):
    __tablename__ = "DanhSachYeuThich"
    # migration 0003; "đúng 1 trong idMonAn/idDiaDiem" do schema kiểm tra
    __table_args__ = (
        UniqueConstraint("idNguoiDung", "idMonAn", name="uq_yt_nguoidung_monan"),
        UniqueConstraint("idNguoiDung", "idDiaDiem", name="uq_yt_nguoidung_diadiem"),
    )

    idDanhSachYeuThich: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36, primary_key=True, default=uuid.uuid4
    )
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_yt_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    idMonAn: Mapped[uuid.UUID | None] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_yt_monan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    idDiaDiem: Mapped[uuid.UUID | None] = mapped_column(
        UUIDChar36,
        ForeignKey("DiaDiem.idDiaDiem", name="fk_yt_diadiem", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
