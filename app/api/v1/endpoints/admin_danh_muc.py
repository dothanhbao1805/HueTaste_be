import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, require_admin
from app.schemas.common import Message
from app.schemas.mon_an import CapNhatDanhMuc, DanhMucAdminOut, TaoDanhMuc
from app.services import danh_muc_service

router = APIRouter(
    prefix="/admin/danh-muc", tags=["Admin - Danh mục món ăn"], dependencies=[Depends(require_admin)]
)


@router.get("", response_model=list[DanhMucAdminOut])
def list_danh_muc(db: DbSession):
    return danh_muc_service.list_admin(db)


@router.post("", response_model=DanhMucAdminOut, status_code=status.HTTP_201_CREATED)
def create_danh_muc(body: TaoDanhMuc, db: DbSession):
    return danh_muc_service.create(db, body)


@router.patch("/{id_danh_muc}", response_model=DanhMucAdminOut)
def update_danh_muc(id_danh_muc: uuid.UUID, body: CapNhatDanhMuc, db: DbSession):
    return danh_muc_service.update(db, id_danh_muc, body)


@router.delete("/{id_danh_muc}", response_model=Message)
def delete_danh_muc(id_danh_muc: uuid.UUID, db: DbSession):
    danh_muc_service.delete(db, id_danh_muc)
    return Message(message="Đã xóa danh mục")
