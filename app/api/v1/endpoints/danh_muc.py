from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.mon_an import CheDoAnOut, DanhMucOut, NguyenLieuItemOut, SoThichOut
from app.services import mon_an_service, so_thich_service

router = APIRouter(tags=["Danh mục"])


@router.get("/danh-muc", response_model=list[DanhMucOut])
def list_danh_muc(db: DbSession):
    return mon_an_service.list_danh_muc(db)


@router.get("/so-thich", response_model=list[SoThichOut])
def list_so_thich(db: DbSession):
    return so_thich_service.list_so_thich(db)


@router.get("/che-do-an", response_model=list[CheDoAnOut])
def list_che_do_an(db: DbSession):
    return so_thich_service.list_che_do_an(db)


@router.get("/nguyen-lieu", response_model=list[NguyenLieuItemOut])
def list_nguyen_lieu(
    db: DbSession,
    q: Annotated[str | None, Query(description="Tên nguyên liệu")] = None,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
):
    """Danh sách nguyên liệu để app chọn 'thành phần cần tránh'."""
    return mon_an_service.list_nguyen_lieu(db, q, size)
