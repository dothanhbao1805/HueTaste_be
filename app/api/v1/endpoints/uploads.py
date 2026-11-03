from enum import StrEnum

from fastapi import APIRouter, Request, UploadFile, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.schemas.nguoi_dung import NguoiDungOut
from app.services import luu_tru_service, nguoi_dung_service

router = APIRouter(tags=["Upload ảnh"])


class LoaiAnh(StrEnum):
    AVATAR = "avatar"
    MON_AN = "mon_an"


class UploadOut(BaseModel):
    url: str


def _luu(request: Request, file: UploadFile, loai: LoaiAnh) -> str:
    # đọc tối đa giới hạn + 1 byte: đủ biết file quá cỡ mà không nạp cả file lớn vào RAM
    gioi_han = int(settings.UPLOAD_MAX_MB * 1024 * 1024)
    duong_dan = luu_tru_service.luu_anh(file.file.read(gioi_han + 1), loai.value)
    return str(request.base_url).rstrip("/") + duong_dan  # app Android dùng thẳng URL tuyệt đối


@router.post("/uploads", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
def upload_anh(request: Request, file: UploadFile, user: CurrentUser, loai: LoaiAnh = LoaiAnh.MON_AN):
    return UploadOut(url=_luu(request, file, loai))


@router.post("/users/me/avatar", response_model=NguoiDungOut)
def upload_avatar(request: Request, file: UploadFile, user: CurrentUser, db: DbSession):
    url = _luu(request, file, LoaiAnh.AVATAR)
    return nguoi_dung_service.update_profile(db, user, ho_ten=None, anh_dai_dien=url)
