import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class CheDoAnNguoiDung(Base):
    __tablename__ = "CheDoAnNguoiDung"
    __table_args__ = (UniqueConstraint("idNguoiDung", "idCheDoAn", name="uq_user_chedoan"),)

    idCheDoAnNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36, primary_key=True, default=uuid.uuid4
    )
    idNguoiDung: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguoiDung.idNguoiDung", name="fk_cdand_nguoidung", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    idCheDoAn: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("CheDoAn.idCheDoAn", name="fk_cdand_chedoan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    ghiChu: Mapped[str | None] = mapped_column(String(255), nullable=True)
