import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class CuocTroChuyen(Base):
    __tablename__ = "CuocTroChuyen"

    idCuocTroChuyen: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_ctc_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    tieuDe: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
