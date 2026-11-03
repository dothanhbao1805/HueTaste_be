import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class DanhMucMonAn(Base):
    __tablename__ = "DanhMucMonAn"
    __table_args__ = (UniqueConstraint("tenDanhMuc", name="uq_danhmuc_ten"),)

    idDanhMucMonAn: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    tenDanhMuc: Mapped[str] = mapped_column(String(150), nullable=False)
    moTa: Mapped[str | None] = mapped_column(Text, nullable=True)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    ngayCapNhat: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )
