from pydantic import BaseModel, Field

from app.core.constants import LoaiThuThap


class YeuCauThuThap(BaseModel):
    loai: LoaiThuThap = LoaiThuThap.TAT_CA
    soMon: int | None = Field(default=None, ge=1, le=300)
