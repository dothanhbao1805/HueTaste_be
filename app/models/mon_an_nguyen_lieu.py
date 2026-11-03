import uuid

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class MonAnNguyenLieu(Base):
    __tablename__ = "MonAnNguyenLieu"
    __table_args__ = (UniqueConstraint("idMonAn", "idNguyenLieu", name="uq_monan_nguyenlieu"),)

    idMonAnNguyenLieu: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36, primary_key=True, default=uuid.uuid4
    )
    idMonAn: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_mannl_monan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idNguyenLieu: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "NguyenLieu.idNguyenLieu", name="fk_mannl_nguyenlieu", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    laThanhPhanChinh: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
