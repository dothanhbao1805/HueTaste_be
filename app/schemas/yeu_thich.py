import uuid

from pydantic import BaseModel, model_validator

from app.schemas.mon_an import DiaDiemOut, MonAnOut


class DoiTuong(BaseModel):
    """Đúng 1 trong idMonAn / idDiaDiem (DB không CHECK được vì FK ON DELETE CASCADE trên MySQL)."""

    idMonAn: uuid.UUID | None = None
    idDiaDiem: uuid.UUID | None = None

    @model_validator(mode="after")
    def _dung_mot(self):
        if (self.idMonAn is None) == (self.idDiaDiem is None):
            raise ValueError("Cần gửi đúng 1 trong idMonAn hoặc idDiaDiem")
        return self


class ThemYeuThich(DoiTuong):
    pass


class YeuThichOut(BaseModel):
    monAn: list[MonAnOut] = []
    diaDiem: list[DiaDiemOut] = []
