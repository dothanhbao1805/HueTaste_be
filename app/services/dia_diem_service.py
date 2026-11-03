import uuid

from sqlalchemy.orm import Session

from app.core.constants import TrangThaiNoiDung
from app.core.exceptions import AppException, NotFoundError
from app.core.geo import bounding_box, haversine_km
from app.models.dia_diem import DiaDiem
from app.models.nguoi_dung import NguoiDung
from app.repositories import anh_repo, dia_diem_repo, yeu_thich_repo
from app.schemas.common import Page
from app.schemas.mon_an import AnhOut, DiaDiemChiTietOut, DiaDiemOut, MonAnOut, MonTaiQuanOut

# Dữ liệu quán ở Huế chỉ vài trăm bản ghi: lọc thô bằng SQL rồi tính khoảng cách + phân trang trong Python
_GIOI_HAN_UNG_VIEN = 2000


def dia_diem_out(dd: DiaDiem, khoang_cach_km: float | None = None) -> DiaDiemOut:
    return DiaDiemOut(
        idDiaDiem=dd.idDiaDiem,
        tenDiaDiem=dd.tenDiaDiem,
        diaChi=dd.diaChi,
        viDo=dd.viDo,
        kinhDo=dd.kinhDo,
        soDienThoai=dd.soDienThoai,
        gioMoCua=dd.gioMoCua,
        mucGia=dd.mucGia,
        diemTrungBinh=dd.diemTrungBinh,
        anhUrl=dd.hinhAnh,  # URL ảnh công khai từ Serper, app tải thẳng
        khoangCachKm=round(khoang_cach_km, 2) if khoang_cach_km is not None else None,
    )


def khoang_cach(dd: DiaDiem, vi_do: float | None, kinh_do: float | None) -> float | None:
    if vi_do is None or kinh_do is None or dd.viDo is None or dd.kinhDo is None:
        return None
    return haversine_km(vi_do, kinh_do, float(dd.viDo), float(dd.kinhDo))


def search(
    db: Session,
    *,
    q: str | None,
    vi_do: float | None,
    kinh_do: float | None,
    ban_kinh_km: float,
    id_mon: uuid.UUID | None,
    page: int,
    size: int,
) -> Page[DiaDiemOut]:
    if (vi_do is None) != (kinh_do is None):
        raise AppException("INVALID_LOCATION", "Cần gửi đủ cả viDo và kinhDo", 400)
    co_vi_tri = vi_do is not None
    bbox = bounding_box(vi_do, kinh_do, ban_kinh_km) if co_vi_tri else None
    ung_vien = dia_diem_repo.search(db, q=q, id_mon=id_mon, bbox=bbox, gioi_han=_GIOI_HAN_UNG_VIEN)

    ket_qua = [(dd, khoang_cach(dd, vi_do, kinh_do)) for dd in ung_vien]
    if co_vi_tri:
        ket_qua = sorted(
            ((dd, d) for dd, d in ket_qua if d is not None and d <= ban_kinh_km), key=lambda x: x[1]
        )
    trang = ket_qua[(page - 1) * size : page * size]
    return Page[DiaDiemOut](
        items=[dia_diem_out(dd, d) for dd, d in trang], total=len(ket_qua), page=page, size=size
    )


def get_active(db: Session, id_dia_diem: uuid.UUID) -> DiaDiem:
    dd = dia_diem_repo.get_by_id(db, id_dia_diem)
    if not dd or dd.trangThai != TrangThaiNoiDung.ACTIVE.value:
        raise NotFoundError("Không tìm thấy địa điểm", "DIA_DIEM_NOT_FOUND")
    return dd


def get_chi_tiet(db: Session, id_dia_diem: uuid.UUID, user: NguoiDung | None = None) -> DiaDiemChiTietOut:
    dd = get_active(db, id_dia_diem)
    return DiaDiemChiTietOut(
        **dia_diem_out(dd).model_dump(),
        maGooglePlace=dd.maGooglePlace,
        anh=[AnhOut.model_validate(a) for a in anh_repo.list_dia_diem(db, id_dia_diem)],
        monAn=[
            MonTaiQuanOut(
                monAn=MonAnOut.model_validate(mon),
                giaBan=int(link.giaBan) if link.giaBan is not None else None,
                laMonDacTrung=link.laMonDacTrung,
            )
            for link, mon in dia_diem_repo.mon_of(db, id_dia_diem)
        ],
        daYeuThich=user is not None
        and yeu_thich_repo.get(db, user.idNguoiDung, id_dia_diem=id_dia_diem) is not None,
    )
