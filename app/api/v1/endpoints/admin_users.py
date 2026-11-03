import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentAdmin, DbSession, require_admin
from app.core.constants import TrangThaiNguoiDung, VaiTro
from app.schemas.common import Page
from app.schemas.nguoi_dung import CapNhatTrangThai, NguoiDungOut
from app.services import nguoi_dung_service

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"], dependencies=[Depends(require_admin)])


@router.get("", response_model=Page[NguoiDungOut])
def list_users(
    db: DbSession,
    q: Annotated[str | None, Query(description="Tìm theo email hoặc họ tên")] = None,
    vaiTro: VaiTro | None = None,
    trangThai: TrangThaiNguoiDung | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return nguoi_dung_service.list_users(
        db,
        q=q,
        vai_tro=vaiTro.value if vaiTro else None,
        trang_thai=trangThai.value if trangThai else None,
        page=page,
        size=size,
    )


@router.get("/{user_id}", response_model=NguoiDungOut)
def get_user(user_id: uuid.UUID, db: DbSession):
    return nguoi_dung_service.get_user(db, user_id)


@router.patch("/{user_id}/status", response_model=NguoiDungOut)
def set_status(user_id: uuid.UUID, body: CapNhatTrangThai, admin: CurrentAdmin, db: DbSession):
    return nguoi_dung_service.set_status(
        db, admin=admin, user_id=user_id, trang_thai=body.trangThai.value
    )
