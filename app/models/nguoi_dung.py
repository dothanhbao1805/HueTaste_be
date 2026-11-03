import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import TrangThaiNguoiDung, VaiTro
from app.db.base import Base
from app.db.types import UUIDChar36


class NguoiDung(Base):
    """Bảng NguoiDung (tài liệu mục II.1.2). Tên cột giữ nguyên theo tài liệu."""

    __tablename__ = "NguoiDung"
    __table_args__ = (UniqueConstraint("email", name="uq_nguoidung_email"),)

    idNguoiDung: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    matKhauMaHoa: Mapped[str] = mapped_column(String(255), nullable=False)
    hoTen: Mapped[str] = mapped_column(String(150), nullable=False)
    anhDaiDien: Mapped[str | None] = mapped_column(Text, nullable=True)
    vaiTro: Mapped[str] = mapped_column(String(30), nullable=False, default=VaiTro.USER.value)
    trangThai: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TrangThaiNguoiDung.ACTIVE.value
    )
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    ngayCapNhat: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )
