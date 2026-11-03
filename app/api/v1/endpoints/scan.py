import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, Request, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.schemas.common import Page
from app.schemas.scan import LichSuScanOut, ScanOut
from app.services import scan_service

router = APIRouter(tags=["Scan món ăn"])


@router.post("/scan", response_model=ScanOut)
def scan_mon(request: Request, file: UploadFile, user: CurrentUser, db: DbSession, background_tasks: BackgroundTasks):
    """Nhận diện món trong ảnh. `DANG_CAP_NHAT`: món Huế mới đang được tìm hiểu, gọi lại GET /scan/{id}."""
    # đọc tối đa giới hạn + 1 byte: đủ biết file quá cỡ mà không nạp cả file lớn vào RAM
    noi_dung = file.file.read(int(settings.UPLOAD_MAX_MB * 1024 * 1024) + 1)
    return scan_service.scan(db, user, noi_dung, str(request.base_url), background_tasks)


@router.get("/scan/{id_lich_su_scan}", response_model=ScanOut)
def get_ket_qua_scan(id_lich_su_scan: uuid.UUID, request: Request, user: CurrentUser, db: DbSession):
    return scan_service.get_ket_qua(db, user, id_lich_su_scan, str(request.base_url))


@router.get("/users/me/lich-su-scan", response_model=Page[LichSuScanOut])
def lich_su_scan(
    request: Request,
    user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return scan_service.lich_su(db, user, page, size, str(request.base_url))
