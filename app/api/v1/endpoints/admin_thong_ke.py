from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_admin
from app.schemas.thong_ke import ThongKeOut
from app.services import thong_ke_service

router = APIRouter(prefix="/admin/thong-ke", tags=["Admin - Thống kê"], dependencies=[Depends(require_admin)])


@router.get("", response_model=ThongKeOut)
def thong_ke(db: DbSession, soNgay: Annotated[int, Query(ge=1, le=90, description="Số ngày gần nhất")] = 7):
    return thong_ke_service.tong_quan(db, soNgay)
