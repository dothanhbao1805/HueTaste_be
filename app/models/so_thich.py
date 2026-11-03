import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class SoThich(Base):
    __tablename__ = "SoThich"
    __table_args__ = (UniqueConstraint("loai", "tenSoThich", name="uq_sothich_loai_ten"),)

    idSoThich: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    loai: Mapped[str] = mapped_column(String(50), nullable=False)
    tenSoThich: Mapped[str] = mapped_column(String(150), nullable=False)
