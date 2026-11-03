from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.deps import require_admin
from app.schemas.common import Message
from app.schemas.thu_thap import YeuCauThuThap
from app.services import thu_thap_service

router = APIRouter(prefix="/admin/thu-thap", tags=["Admin - Thu thập dữ liệu"], dependencies=[Depends(require_admin)])


@router.post("", response_model=Message, status_code=status.HTTP_202_ACCEPTED)
def bat_dau_thu_thap(body: YeuCauThuThap, background_tasks: BackgroundTasks):
    # Chạy sau khi trả response; thu_thap_service.chay tự mở session riêng và giữ khoá GET_LOCK
    background_tasks.add_task(thu_thap_service.chay, body.loai, body.soMon)
    return Message(message="Đã bắt đầu thu thập dữ liệu, xem tiến độ trong log server")
