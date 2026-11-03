import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import Message
from app.schemas.danh_gia import DanhGiaOut, VietDanhGia
from app.services import danh_gia_service

router = APIRouter(prefix="/danh-gia", tags=["Đánh giá"])


@router.post("", response_model=DanhGiaOut, status_code=status.HTTP_201_CREATED)
def viet_danh_gia(body: VietDanhGia, user: CurrentUser, db: DbSession):
    return danh_gia_service.viet(db, user, body)


@router.delete("/{id_danh_gia}", response_model=Message)
def xoa_danh_gia(id_danh_gia: uuid.UUID, user: CurrentUser, db: DbSession):
    danh_gia_service.xoa(db, user, id_danh_gia)
    return Message(message="Đã xóa đánh giá")
