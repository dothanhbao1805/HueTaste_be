import uuid
from datetime import date

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import Message
from app.schemas.mon_an import CapNhatCheDoAn, CapNhatSoThich, CheDoAnNguoiDungOut, SoThichNguoiDungOut
from app.schemas.nguoi_dung import CapNhatThongTin, DoiMatKhau, NguoiDungOut
from app.schemas.nhu_cau import CapNhatNhuCau, NhuCauOut
from app.services import nguoi_dung_service, nhu_cau_service, so_thich_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=NguoiDungOut)
def get_me(user: CurrentUser):
    return user


@router.patch("/me", response_model=NguoiDungOut)
def update_me(body: CapNhatThongTin, user: CurrentUser, db: DbSession):
    return nguoi_dung_service.update_profile(
        db, user, ho_ten=body.hoTen, anh_dai_dien=body.anhDaiDien
    )


@router.post("/me/change-password", response_model=Message)
def change_password(body: DoiMatKhau, user: CurrentUser, db: DbSession):
    nguoi_dung_service.change_password(
        db, user, mat_khau_cu=body.matKhauCu, mat_khau_moi=body.matKhauMoi
    )
    return Message(message="Đổi mật khẩu thành công")


@router.get("/me/so-thich", response_model=list[SoThichNguoiDungOut])
def get_my_so_thich(user: CurrentUser, db: DbSession):
    return so_thich_service.get_so_thich_cua_toi(db, user)


@router.put("/me/so-thich", response_model=list[SoThichNguoiDungOut])
def set_my_so_thich(body: CapNhatSoThich, user: CurrentUser, db: DbSession):
    return so_thich_service.set_so_thich_cua_toi(db, user, body.soThich)


@router.get("/me/che-do-an", response_model=list[CheDoAnNguoiDungOut])
def get_my_che_do_an(user: CurrentUser, db: DbSession):
    return so_thich_service.get_che_do_an_cua_toi(db, user)


@router.put("/me/che-do-an", response_model=list[CheDoAnNguoiDungOut])
def set_my_che_do_an(body: CapNhatCheDoAn, user: CurrentUser, db: DbSession):
    return so_thich_service.set_che_do_an_cua_toi(db, user, body.cheDoAn)


@router.get("/me/nhu-cau", response_model=list[NhuCauOut])
def get_my_nhu_cau(user: CurrentUser, db: DbSession, ngay: date | None = None):
    return nhu_cau_service.list_cua_toi(db, user, ngay)


@router.put("/me/nhu-cau", response_model=NhuCauOut)
def set_my_nhu_cau(body: CapNhatNhuCau, user: CurrentUser, db: DbSession):
    return nhu_cau_service.cap_nhat(db, user, body)


@router.delete("/me/nhu-cau/{id_nhu_cau}", response_model=Message)
def delete_my_nhu_cau(id_nhu_cau: uuid.UUID, user: CurrentUser, db: DbSession):
    nhu_cau_service.xoa(db, user, id_nhu_cau)
    return Message(message="Đã xóa nhu cầu")
