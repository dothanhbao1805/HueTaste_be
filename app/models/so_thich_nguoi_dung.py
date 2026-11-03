import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class SoThichNguoiDung(Base):
    __tablename__ = "SoThichNguoiDung"
    __table_args__ = (
        UniqueConstraint("idNguoiDung", "idSoThich", name="uq_user_sothich"),
        CheckConstraint("mucDo between 1 and 5", name="chk_stnd_mucdo"),
    )

    idSoThichNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36, primary_key=True, default=uuid.uuid4
    )
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_stnd_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    idSoThich: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("SoThich.idSoThich", name="fk_stnd_sothich", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    mucDo: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default=text("3"))
