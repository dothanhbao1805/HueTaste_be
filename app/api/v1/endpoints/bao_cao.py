from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.bao_cao import BaoCaoOut, GuiBaoCao
from app.schemas.common import Page
from app.services import bao_cao_service

router = APIRouter(tags=["Báo cáo"])


@router.post("/bao-cao", response_model=BaoCaoOut, status_code=status.HTTP_201_CREATED)
def gui_bao_cao(body: GuiBaoCao, user: CurrentUser, db: DbSession):
    return bao_cao_service.gui(db, user, body)


@router.get("/users/me/bao-cao", response_model=Page[BaoCaoOut])
def list_bao_cao_cua_toi(
    user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return bao_cao_service.list_cua_toi(db, user, page, size)
