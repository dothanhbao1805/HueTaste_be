import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DbSession, OptionalUser
from app.schemas.common import Page
from app.schemas.danh_gia import TrangDanhGiaOut
from app.schemas.mon_an import MonAnChiTietOut, MonAnOut
from app.services import danh_gia_service, mon_an_service

router = APIRouter(prefix="/mon-an", tags=["Món ăn"])


@router.get("", response_model=Page[MonAnOut])
def search_mon_an(
    db: DbSession,
    q: Annotated[str | None, Query(description="Tên món, gõ có hoặc không dấu")] = None,
    idDanhMucMonAn: uuid.UUID | None = None,
    nguyenLieu: Annotated[str | None, Query(description="Tên nguyên liệu")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return mon_an_service.search(
        db, q=q, id_danh_muc=idDanhMucMonAn, nguyen_lieu=nguyenLieu, page=page, size=size
    )


@router.get("/{id_mon_an}", response_model=MonAnChiTietOut)
def get_mon_an(id_mon_an: uuid.UUID, db: DbSession, user: OptionalUser):
    return mon_an_service.get_chi_tiet(db, id_mon_an, user)


@router.get("/{id_mon_an}/danh-gia", response_model=TrangDanhGiaOut)
def list_danh_gia(
    id_mon_an: uuid.UUID,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return danh_gia_service.list_mon(db, id_mon_an, page, size)
