import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_admin
from app.core.constants import TrangThaiBaoCao
from app.schemas.bao_cao import BaoCaoOut, XuLyBaoCao
from app.schemas.common import Page
from app.services import bao_cao_service

router = APIRouter(prefix="/admin/bao-cao", tags=["Admin - Báo cáo"], dependencies=[Depends(require_admin)])


@router.get("", response_model=Page[BaoCaoOut])
def list_bao_cao(
    db: DbSession,
    trangThai: TrangThaiBaoCao | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return bao_cao_service.list_admin(db, trangThai.value if trangThai else None, page, size)


@router.get("/{id_bao_cao}", response_model=BaoCaoOut)
def get_bao_cao(id_bao_cao: uuid.UUID, db: DbSession):
    return bao_cao_service.get_admin(db, id_bao_cao)


@router.post("/{id_bao_cao}/xu-ly", response_model=BaoCaoOut)
def xu_ly_bao_cao(id_bao_cao: uuid.UUID, body: XuLyBaoCao, db: DbSession):
    return bao_cao_service.xu_ly(db, id_bao_cao, body)
