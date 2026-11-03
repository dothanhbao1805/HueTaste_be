"""Danh mục sở thích/chế độ ăn và lựa chọn của người dùng (đầu vào cho gợi ý)."""
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, NotFoundError
from app.models.nguoi_dung import NguoiDung
from app.repositories import che_do_an_repo, so_thich_repo
from app.schemas.mon_an import (
    CheDoAnNguoiDungIn,
    CheDoAnNguoiDungOut,
    CheDoAnOut,
    SoThichNguoiDungIn,
    SoThichNguoiDungOut,
    SoThichOut,
)


def list_so_thich(db: Session) -> list[SoThichOut]:
    return [SoThichOut.model_validate(s) for s in so_thich_repo.list_all(db)]


def list_che_do_an(db: Session) -> list[CheDoAnOut]:
    return [CheDoAnOut.model_validate(c) for c in che_do_an_repo.list_all(db)]


def get_so_thich_cua_toi(db: Session, user: NguoiDung) -> list[SoThichNguoiDungOut]:
    return [
        SoThichNguoiDungOut(idSoThich=st.idSoThich, loai=st.loai, tenSoThich=st.tenSoThich, mucDo=link.mucDo)
        for link, st in so_thich_repo.list_of_user(db, user.idNguoiDung)
    ]


def set_so_thich_cua_toi(
    db: Session, user: NguoiDung, items: list[SoThichNguoiDungIn]
) -> list[SoThichNguoiDungOut]:
    ids = [i.idSoThich for i in items]
    if len(set(ids)) != len(ids):
        raise AppException("DUPLICATE_ITEM", "Danh sách sở thích bị lặp", 400)
    if len(so_thich_repo.get_many(db, ids)) != len(ids):
        raise NotFoundError("Có sở thích không tồn tại", "SO_THICH_NOT_FOUND")
    so_thich_repo.replace_of_user(db, user.idNguoiDung, [(i.idSoThich, i.mucDo) for i in items])
    db.commit()
    return get_so_thich_cua_toi(db, user)


def get_che_do_an_cua_toi(db: Session, user: NguoiDung) -> list[CheDoAnNguoiDungOut]:
    return [
        CheDoAnNguoiDungOut(idCheDoAn=cd.idCheDoAn, tenCheDo=cd.tenCheDo, moTa=cd.moTa, ghiChu=link.ghiChu)
        for link, cd in che_do_an_repo.list_of_user(db, user.idNguoiDung)
    ]


def set_che_do_an_cua_toi(
    db: Session, user: NguoiDung, items: list[CheDoAnNguoiDungIn]
) -> list[CheDoAnNguoiDungOut]:
    ids = [i.idCheDoAn for i in items]
    if len(set(ids)) != len(ids):
        raise AppException("DUPLICATE_ITEM", "Danh sách chế độ ăn bị lặp", 400)
    if len(che_do_an_repo.get_many(db, ids)) != len(ids):
        raise NotFoundError("Có chế độ ăn không tồn tại", "CHE_DO_AN_NOT_FOUND")
    che_do_an_repo.replace_of_user(db, user.idNguoiDung, [(i.idCheDoAn, i.ghiChu) for i in items])
    db.commit()
    return get_che_do_an_cua_toi(db, user)
