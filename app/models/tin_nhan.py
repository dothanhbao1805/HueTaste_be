import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class TinNhan(Base):
    __tablename__ = "TinNhan"

    idTinNhan: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idCuocTroChuyen: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "CuocTroChuyen.idCuocTroChuyen", name="fk_tn_cuoctro", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    idGoiY: Mapped[uuid.UUID | None] = mapped_column(
        UUIDChar36,
        ForeignKey("GoiY.idGoiY", name="fk_tn_goiy", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    nguoiGui: Mapped[str] = mapped_column(String(30), nullable=False)
    noiDung: Mapped[str] = mapped_column(Text, nullable=False)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    loaiNoiDung: Mapped[str] = mapped_column(
        String(30), nullable=False, default="text", server_default=text("'text'")
    )
