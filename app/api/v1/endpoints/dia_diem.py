import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DbSession, OptionalUser
from app.schemas.common import Page
from app.schemas.danh_gia import TrangDanhGiaOut
from app.schemas.mon_an import DiaDiemChiTietOut, DiaDiemOut
from app.services import danh_gia_service, dia_diem_service

router = APIRouter(prefix="/dia-diem", tags=["Địa điểm"])


@router.get("", response_model=Page[DiaDiemOut])
def search_dia_diem(
    db: DbSession,
    q: Annotated[str | None, Query(description="Tên quán")] = None,
    viDo: Annotated[float | None, Query(ge=-90, le=90)] = None,
    kinhDo: Annotated[float | None, Query(ge=-180, le=180)] = None,
    banKinhKm: Annotated[float, Query(gt=0, le=50)] = 5,
    idMonAn: uuid.UUID | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return dia_diem_service.search(
        db,
        q=q,
        vi_do=viDo,
        kinh_do=kinhDo,
        ban_kinh_km=banKinhKm,
        id_mon=idMonAn,
        page=page,
        size=size,
    )


@router.get("/{id_dia_diem}", response_model=DiaDiemChiTietOut)
def get_dia_diem(id_dia_diem: uuid.UUID, db: DbSession, user: OptionalUser):
    return dia_diem_service.get_chi_tiet(db, id_dia_diem, user)


@router.get("/{id_dia_diem}/danh-gia", response_model=TrangDanhGiaOut)
def list_danh_gia(
    id_dia_diem: uuid.UUID,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return danh_gia_service.list_quan(db, id_dia_diem, page, size)
