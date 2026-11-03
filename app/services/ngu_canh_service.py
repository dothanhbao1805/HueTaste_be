from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.am_lich import la_ngay_ram
from app.core.config import settings
from app.core.constants import Buoi
from app.models.ngu_canh import NguCanh
from app.models.nguoi_dung import NguoiDung
from app.repositories import goi_y_repo, nhu_cau_repo
from app.schemas.goi_y import YeuCauGoiY
from app.services import thoi_tiet_service

TZ_VN = ZoneInfo("Asia/Ho_Chi_Minh")
CUA_SO_GIO_AN = timedelta(hours=2)  # lệch tối đa giữa giờ hiện tại và giờ ăn đã đặt để coi là bữa đó


def buoi_theo_gio(gio: int) -> Buoi:
    if 5 <= gio < 10:
        return Buoi.SANG
    if 10 <= gio < 14:
        return Buoi.TRUA
    if 14 <= gio < 17:
        return Buoi.CHIEU
    if 17 <= gio < 21:
        return Buoi.TOI
    return Buoi.KHUYA


def _toa_do(v: float | None) -> Decimal | None:
    return None if v is None else Decimal(str(round(v, 7)))


def xac_dinh_bua(db: Session, user: NguoiDung, now: datetime) -> str | None:
    """Bữa có giờ ăn người dùng đặt hôm nay gần `now` nhất (lệch tối đa CUA_SO_GIO_AN); không có thì None."""
    gan_nhat: tuple[timedelta, str] | None = None
    for nc in nhu_cau_repo.list_theo_ngay(db, user.idNguoiDung, now.date()):
        if nc.gioAn is None or not nc.buaAn:
            continue
        lech = abs(datetime.combine(now.date(), nc.gioAn) - now.replace(tzinfo=None))
        if lech <= CUA_SO_GIO_AN and (gan_nhat is None or lech < gan_nhat[0]):
            gan_nhat = (lech, nc.buaAn)
    return gan_nhat[1] if gan_nhat else None


def bo_sung_tu_nhu_cau(db: Session, user: NguoiDung, req: YeuCauGoiY, now: datetime | None = None) -> YeuCauGoiY:
    """Không gửi buaAn thì lấy bữa theo giờ ăn đã đặt; điền nganSach/ghiChu/nguyenLieuTranh còn thiếu
    từ nhu cầu người dùng đã lưu cho bữa này hôm nay."""
    now = now or datetime.now(TZ_VN)
    if req.buaAn is None and (bua := xac_dinh_bua(db, user, now)):
        req = req.model_copy(update={"buaAn": bua})
    nc = nhu_cau_repo.get(db, user.idNguoiDung, now.date(), req.buaAn or buoi_theo_gio(now.hour).value)
    if nc is None:
        return req
    ngan_sach = req.nganSach
    if ngan_sach is None and nc.nganSach is not None:
        ngan_sach = int(nc.nganSach)
    tranh = req.nguyenLieuTranh if req.nguyenLieuTranh is not None else nhu_cau_repo.tach_ids(nc.nguyenLieuTranh)
    return req.model_copy(update={"nganSach": ngan_sach, "ghiChu": req.ghiChu or nc.ghiChu, "nguyenLieuTranh": tranh})


def tao_ngu_canh(db: Session, user: NguoiDung, req: YeuCauGoiY, now: datetime | None = None) -> NguCanh:
    """Ghi nhận ngữ cảnh hiện tại (NguCanh) + nhu cầu người dùng nhập (NhuCauTheoNgay). Không commit."""
    now = now or datetime.now(TZ_VN)
    buoi = req.buaAn if req.buaAn in {b.value for b in Buoi} else buoi_theo_gio(now.hour).value

    # không có vị trí thì lấy thời tiết ở trung tâm Huế
    vi_do = req.viDo if req.viDo is not None else settings.HUE_VI_DO
    kinh_do = req.kinhDo if req.kinhDo is not None else settings.HUE_KINH_DO
    thoi_tiet = thoi_tiet_service.lay_thoi_tiet(vi_do, kinh_do)

    nhu_cau = None
    if req.buaAn or req.nganSach is not None or req.ghiChu or req.nguyenLieuTranh:
        # chỉ ghi các trường request có, giữ nguyên giờ ăn đã đặt
        truong = {"nganSach": req.nganSach, "ghiChu": req.ghiChu}
        if req.nguyenLieuTranh is not None:
            truong["nguyenLieuTranh"] = nhu_cau_repo.ghep_ids(req.nguyenLieuTranh)
        nhu_cau = nhu_cau_repo.upsert(db, user.idNguoiDung, now.date(), req.buaAn or buoi, **truong)
    return goi_y_repo.create_ngu_canh(
        db,
        idNguoiDung=user.idNguoiDung,
        idNhuCauTheoNgay=nhu_cau.idNhuCauTheoNgay if nhu_cau else None,
        viDo=_toa_do(req.viDo),
        kinhDo=_toa_do(req.kinhDo),
        nhietDo=Decimal(str(round(thoi_tiet["nhietDo"], 2))) if thoi_tiet else None,
        thoiTiet=thoi_tiet["thoiTiet"] if thoi_tiet else None,
        buoiTrongNgay=buoi,
        laNgayRam=la_ngay_ram(now.date()),
    )
