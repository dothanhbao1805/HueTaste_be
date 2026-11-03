from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_admin
from app.schemas.scan import MonScanKhongLuuOut
from app.services import scan_service

router = APIRouter(prefix="/admin/scan", tags=["Admin - Scan"], dependencies=[Depends(require_admin)])


@router.get("/mon-khong-luu", response_model=list[MonScanKhongLuuOut])
def mon_khong_luu(db: DbSession):
    """Món người dùng hay scan nhưng không phải đặc trưng Huế nên không lưu vào MonAn."""
    return scan_service.list_mon_khong_luu(db)
