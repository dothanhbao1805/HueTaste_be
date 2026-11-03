import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class NguyenLieu(Base):
    __tablename__ = "NguyenLieu"
    __table_args__ = (UniqueConstraint("tenNguyenLieu", name="uq_nguyenlieu_ten"),)

    idNguyenLieu: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    tenNguyenLieu: Mapped[str] = mapped_column(String(150), nullable=False)
    nhomNguyenLieu: Mapped[str | None] = mapped_column(String(100), nullable=True)
