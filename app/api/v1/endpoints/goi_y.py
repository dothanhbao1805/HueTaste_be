from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.goi_y import KetQuaGoiYOut, YeuCauGoiY
from app.services import goi_y_service

router = APIRouter(prefix="/goi-y", tags=["Gợi ý"])


@router.post("", response_model=KetQuaGoiYOut)
def goi_y(body: YeuCauGoiY, user: CurrentUser, db: DbSession):
    """Gợi ý món + quán theo ngữ cảnh hiện tại (giờ, thời tiết, âm lịch, vị trí) và hồ sơ người dùng."""
    return goi_y_service.goi_y(db, user, body)
