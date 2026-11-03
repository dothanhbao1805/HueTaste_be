from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_bao_cao,
    admin_scan,
    admin_danh_muc,
    admin_thong_ke,
    admin_thu_thap,
    admin_users,
    auth,
    bao_cao,
    danh_gia,
    danh_muc,
    dia_diem,
    goi_y,
    mon_an,
    scan,
    uploads,
    users,
    yeu_thich,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(yeu_thich.router)
api_router.include_router(danh_muc.router)
api_router.include_router(mon_an.router)
api_router.include_router(dia_diem.router)
api_router.include_router(goi_y.router)
api_router.include_router(danh_gia.router)
api_router.include_router(bao_cao.router)
api_router.include_router(uploads.router)
api_router.include_router(scan.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_danh_muc.router)
api_router.include_router(admin_bao_cao.router)
api_router.include_router(admin_thong_ke.router)
api_router.include_router(admin_thu_thap.router)
api_router.include_router(admin_scan.router)
