import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, DateTime, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class TokenDatLaiMatKhau(Base):
    """Bảng TokenDatLaiMatKhau (tài liệu mục II.2.2).

    `maToken` lưu hash SHA-256 của token gửi qua email, không lưu token gốc.
    """

    __tablename__ = "TokenDatLaiMatKhau"
    __table_args__ = (UniqueConstraint("maToken", name="uq_token_matoken"),)

    idTokenDatLaiMatKhau: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36, primary_key=True, default=uuid.uuid4
    )
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_token_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    maToken: Mapped[str] = mapped_column(String(255), nullable=False)
    hetHanLuc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    daSuDung: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
