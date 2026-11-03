import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.core.constants import LoaiGoiY
from app.schemas.common import Message
from app.schemas.yeu_thich import ThemYeuThich, YeuThichOut
from app.services import yeu_thich_service

router = APIRouter(prefix="/users/me/yeu-thich", tags=["Yêu thích"])


@router.get("", response_model=YeuThichOut)
def list_yeu_thich(user: CurrentUser, db: DbSession, loai: LoaiGoiY | None = None):
    return yeu_thich_service.list_cua_toi(db, user, loai)


@router.post("", response_model=Message, status_code=status.HTTP_201_CREATED)
def them_yeu_thich(body: ThemYeuThich, user: CurrentUser, db: DbSession):
    yeu_thich_service.them(db, user, body)
    return Message(message="Đã thêm vào yêu thích")


@router.delete("/mon-an/{id_mon_an}", response_model=Message)
def xoa_mon_yeu_thich(id_mon_an: uuid.UUID, user: CurrentUser, db: DbSession):
    yeu_thich_service.xoa(db, user, id_mon=id_mon_an)
    return Message(message="Đã bỏ yêu thích")


@router.delete("/dia-diem/{id_dia_diem}", response_model=Message)
def xoa_quan_yeu_thich(id_dia_diem: uuid.UUID, user: CurrentUser, db: DbSession):
    yeu_thich_service.xoa(db, user, id_dia_diem=id_dia_diem)
    return Message(message="Đã bỏ yêu thích")
