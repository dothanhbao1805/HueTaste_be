import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class ChiTietBaoCao(Base):
    __tablename__ = "ChiTietBaoCao"
    __table_args__ = (UniqueConstraint("idBaoCao", "idMonAn", name="uq_ctbc"),)

    idChiTietBaoCao: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idBaoCao: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("BaoCao.idBaoCao", name="fk_ctbc_baocao", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idMonAn: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey("MonAn.idMonAn", name="fk_ctbc_monan", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    ketQuaXuLy: Mapped[str | None] = mapped_column(String(255), nullable=True)
