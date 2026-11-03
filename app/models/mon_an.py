import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDChar36


class MonAn(Base):
    __tablename__ = "MonAn"
    # tenChuanHoa / maWikipedia chống trùng khi pipeline thu thập chạy lại (migration 0002)
    __table_args__ = (
        UniqueConstraint("tenChuanHoa", name="uq_monan_tenchuanhoa"),
        UniqueConstraint("maWikipedia", name="uq_monan_mawikipedia"),
    )

    idMonAn: Mapped[uuid.UUID] = mapped_column(UUIDChar36, primary_key=True, default=uuid.uuid4)
    idDanhMucMonAn: Mapped[uuid.UUID] = mapped_column(
        UUIDChar36,
        ForeignKey(
            "DanhMucMonAn.idDanhMucMonAn",
            name="fk_monan_danhmuc",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    tenMon: Mapped[str] = mapped_column(String(255), nullable=False)
    moTa: Mapped[str | None] = mapped_column(Text, nullable=True)
    hinhAnh: Mapped[str | None] = mapped_column(Text, nullable=True)
    buoiPhuHop: Mapped[str | None] = mapped_column(String(50), nullable=True)
    thoiTietPhuHop: Mapped[str | None] = mapped_column(String(50), nullable=True)
    giaThamKhaoTu: Mapped[Decimal | None] = mapped_column(Numeric(12, 0), nullable=True)
    giaThamKhaoDen: Mapped[Decimal | None] = mapped_column(Numeric(12, 0), nullable=True)
    trangThai: Mapped[str] = mapped_column(String(30), nullable=False)
    tenChuanHoa: Mapped[str] = mapped_column(String(255), nullable=False)
    maWikipedia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nguonThamKhao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ngayTao: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    ngayCapNhat: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )
