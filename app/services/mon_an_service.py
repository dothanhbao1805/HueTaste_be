import uuid

from sqlalchemy.orm import Session

from app.core.constants import TrangThaiNoiDung
from app.core.exceptions import NotFoundError
from app.models.mon_an import MonAn
from app.models.nguoi_dung import NguoiDung
from app.repositories import (
    anh_repo,
    che_do_an_repo,
    danh_muc_repo,
    dia_diem_repo,
    mon_an_repo,
    nguyen_lieu_repo,
    yeu_thich_repo,
)
from app.schemas.common import Page
from app.schemas.mon_an import (
    AnhOut,
    CheDoAnOut,
    DanhMucOut,
    MonAnChiTietOut,
    MonAnOut,
    NguyenLieuItemOut,
    NguyenLieuOut,
    QuanBanMonOut,
    TagMonOut,
)
from app.services.dia_diem_service import dia_diem_out


def list_danh_muc(db: Session) -> list[DanhMucOut]:
    return [DanhMucOut.model_validate(d) for d in danh_muc_repo.list_all(db)]


def list_nguyen_lieu(db: Session, q: str | None, size: int) -> list[NguyenLieuItemOut]:
    return [NguyenLieuItemOut.model_validate(nl) for nl in nguyen_lieu_repo.search(db, q, size)]


def search(
    db: Session,
    *,
    q: str | None,
    id_danh_muc: uuid.UUID | None,
    nguyen_lieu: str | None,
    page: int,
    size: int,
) -> Page[MonAnOut]:
    items, total = mon_an_repo.search(
        db, q=q, id_danh_muc=id_danh_muc, nguyen_lieu=nguyen_lieu, page=page, size=size
    )
    return Page[MonAnOut](
        items=[MonAnOut.model_validate(m) for m in items], total=total, page=page, size=size
    )


def get_active(db: Session, id_mon: uuid.UUID) -> MonAn:
    mon = mon_an_repo.get_by_id(db, id_mon)
    if not mon or mon.trangThai != TrangThaiNoiDung.ACTIVE.value:
        raise NotFoundError("Không tìm thấy món ăn", "MON_AN_NOT_FOUND")
    return mon


def get_chi_tiet(db: Session, id_mon: uuid.UUID, user: NguoiDung | None = None) -> MonAnChiTietOut:
    mon = get_active(db, id_mon)

    danh_muc = danh_muc_repo.get_by_id(db, mon.idDanhMucMonAn)
    nguyen_lieu = [
        NguyenLieuOut(
            idNguyenLieu=nl.idNguyenLieu,
            tenNguyenLieu=nl.tenNguyenLieu,
            nhomNguyenLieu=nl.nhomNguyenLieu,
            laThanhPhanChinh=chinh,
        )
        for nl, chinh in mon_an_repo.nguyen_lieu_of(db, id_mon)
    ]
    tags = [
        TagMonOut(idSoThich=st.idSoThich, loai=st.loai, tenSoThich=st.tenSoThich, trongSo=ts)
        for st, ts in mon_an_repo.so_thich_of(db, [id_mon]).get(id_mon, [])
    ]
    ids_che_do = mon_an_repo.che_do_an_of(db, [id_mon]).get(id_mon, set())
    che_do = [CheDoAnOut.model_validate(c) for c in che_do_an_repo.get_many(db, list(ids_che_do))]
    quan = sorted(
        dia_diem_repo.quan_of_mons(db, [id_mon]),
        key=lambda x: (not x[0].laMonDacTrung, -(float(x[1].diemTrungBinh or 0))),
    )
    anh = [AnhOut.model_validate(a) for a in anh_repo.list_mon(db, id_mon)]
    if mon.hinhAnh and all(a.url != mon.hinhAnh for a in anh):
        anh.insert(0, AnhOut(url=mon.hinhAnh))  # ảnh bìa luôn đứng đầu gallery
    return MonAnChiTietOut(
        **MonAnOut.model_validate(mon).model_dump(),
        anh=anh,
        danhMuc=DanhMucOut.model_validate(danh_muc) if danh_muc else None,
        nguyenLieu=nguyen_lieu,
        soThich=tags,
        cheDoAn=che_do,
        diaDiem=[
            QuanBanMonOut(
                diaDiem=dia_diem_out(dd),
                giaBan=int(link.giaBan) if link.giaBan is not None else None,
                laMonDacTrung=link.laMonDacTrung,
            )
            for link, dd in quan
        ],
        daYeuThich=user is not None and yeu_thich_repo.get(db, user.idNguoiDung, id_mon=id_mon) is not None,
    )
