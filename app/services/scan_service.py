"""Scan ảnh món ăn: model vision nhận diện -> so khớp MonAn -> lưu LichSuScan.

Món Huế chưa có trong DB được tạo `unverified` rồi tìm hiểu nền (thu_thap_service.lam_giau_mon);
món không đặc trưng Huế chỉ trả thông tin cơ bản, không lưu vào MonAn.
"""
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.chuan_hoa import chuan_hoa_ten, do_tuong_dong
from app.core.config import settings
from app.core.constants import DANH_MUC_MON, TrangThaiNoiDung
from app.core.exceptions import AppException, NotFoundError
from app.models.lich_su_scan import LichSuScan
from app.models.mon_an import MonAn
from app.models.nguoi_dung import NguoiDung
from app.repositories import danh_muc_repo, lich_su_scan_repo, mon_an_repo
from app.schemas.common import Page
from app.schemas.mon_an import MonAnOut
from app.schemas.scan import LichSuScanOut, MonScanKhongLuuOut, ScanOut, TrangThaiScan
from app.services import gemini_service, luu_tru_service, mon_an_service, thu_thap_service

logger = logging.getLogger(__name__)

KHAC = "KHAC"
_NGUONG_KHOP = 0.85
_MIME = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
_THU_LAI_SAU_GIAY = 24 * 3600  # món unverified được tìm hiểu lại tối đa 1 lần/ngày

# Theo dõi trong tiến trình: món đang tìm hiểu nền (bắt đầu lúc) và lần thử cuối. Background task
# chạy cùng tiến trình API nên đủ dùng; tiến trình khởi động lại thì món có thể được thử thêm 1 lần.
_dang_lam_giau: dict[uuid.UUID, float] = {}
_lan_thu_cuoi: dict[uuid.UUID, float] = {}


def _schema(ten_mon: list[str], danh_muc: list[str]) -> dict[str, Any]:
    ten = [*ten_mon, KHAC]
    return {
        "type": "OBJECT",
        "properties": {
            "laMonAn": {"type": "BOOLEAN"},
            "tenMonTrongDanhSach": {"type": "STRING", "enum": ten},
            "tenMonThucTe": {"type": "STRING"},
            "laMonDacTrungHue": {"type": "BOOLEAN"},
            "danhMuc": {"type": "STRING", "enum": danh_muc},
            "doTinCay": {"type": "NUMBER"},
            "moTaNgan": {"type": "STRING"},
            "monGanGiong": {"type": "ARRAY", "items": {"type": "STRING", "enum": ten}},
        },
        "required": ["laMonAn", "tenMonTrongDanhSach", "tenMonThucTe", "laMonDacTrungHue", "doTinCay"],
    }


def _prompt(ten_mon: list[str], danh_muc: list[str]) -> str:
    return (
        "Bạn là chuyên gia ẩm thực xứ Huế (Việt Nam). Nhìn ảnh và trả lời:\n"
        "1. laMonAn: ảnh có phải món ăn/đồ uống không?\n"
        f"2. tenMonTrongDanhSach: chọn ĐÚNG một tên trong danh sách món sau; không có thì ghi \"{KHAC}\": "
        + "; ".join(ten_mon or ["(trống)"])
        + "\n3. tenMonThucTe: tên tiếng Việt có dấu phổ biến nhất của món trong ảnh.\n"
        "4. laMonDacTrungHue: đây có phải món ăn đặc trưng / phổ biến của thành phố Huế không? "
        "Chỉ true khi món thực sự gắn với ẩm thực Huế (vd bún bò Huế, cơm hến, bánh khoái), "
        "false với món phổ biến nơi khác (phở, pizza, bánh mì...).\n"
        f"5. danhMuc: chọn trong: {'; '.join(danh_muc)}.\n"
        "6. doTinCay: 0..1. 7. moTaNgan: 1-2 câu giới thiệu món. "
        "8. monGanGiong: tối đa 3 tên trong danh sách giống món này nhất.\n"
        "Chỉ trả JSON đúng các trường trên."
    )


def _tim_mon(kq: dict[str, Any], ds: list[MonAn]) -> MonAn | None:
    theo_khoa = {m.tenChuanHoa: m for m in ds}
    ten_chon = (kq.get("tenMonTrongDanhSach") or "").strip()
    if ten_chon and ten_chon != KHAC and (m := theo_khoa.get(chuan_hoa_ten(ten_chon))):
        return m
    # model chọn KHAC/viết lệch tên: so gần đúng thêm 1 lớp để không tạo trùng món đã có
    tot, diem_tot = None, 0.0
    for ten in {ten_chon, kq.get("tenMonThucTe") or ""} - {"", KHAC}:
        for m in ds:
            if (d := do_tuong_dong(ten, m.tenMon)) > diem_tot:
                tot, diem_tot = m, d
    return tot if diem_tot >= _NGUONG_KHOP else None


def _ten_danh_muc(db: Session) -> list[str]:
    return [d.tenDanhMuc for d in danh_muc_repo.list_all(db)] or list(DANH_MUC_MON)


def _tao_mon(db: Session, kq: dict[str, Any], danh_muc: list[str]) -> MonAn:
    ten = kq["tenMonThucTe"].strip()[:255]
    dm = danh_muc_repo.get_or_create(db, kq.get("danhMuc") if kq.get("danhMuc") in danh_muc else "Món mặn khác")
    khoa = chuan_hoa_ten(ten)
    try:
        with db.begin_nested():
            return mon_an_repo.create(
                db,
                tenMon=ten,
                tenChuanHoa=khoa,
                moTa=(kq.get("moTaNgan") or None),
                idDanhMucMonAn=dm.idDanhMucMonAn,
                trangThai=TrangThaiNoiDung.UNVERIFIED.value,
            )
    except IntegrityError:
        # người khác vừa scan cùng món: dùng bản đã tạo
        mon = mon_an_repo.get_by_ten_chuan_hoa(db, [khoa])
        if mon is None:
            raise
        return mon


def _lam_giau(id_mon: uuid.UUID) -> None:
    try:
        thu_thap_service.lam_giau_mon(id_mon)
    finally:
        _dang_lam_giau.pop(id_mon, None)
        _lan_thu_cuoi[id_mon] = time.monotonic()


def _len_lich_lam_giau(background_tasks: BackgroundTasks, mon: MonAn) -> bool:
    if mon.idMonAn in _dang_lam_giau:
        return True
    cuoi = _lan_thu_cuoi.get(mon.idMonAn)
    if cuoi is not None and time.monotonic() - cuoi < _THU_LAI_SAU_GIAY:
        return False
    _dang_lam_giau[mon.idMonAn] = time.monotonic()
    background_tasks.add_task(_lam_giau, mon.idMonAn)
    return True


def _dang_cap_nhat(id_mon: uuid.UUID) -> bool:
    bat_dau = _dang_lam_giau.get(id_mon)
    return bat_dau is not None and time.monotonic() - bat_dau < settings.SCAN_CHO_LAM_GIAU_GIAY


def _url(base_url: str, duong_dan: str) -> str:
    return base_url.rstrip("/") + duong_dan  # app Android dùng thẳng URL tuyệt đối


def _ket_qua(db: Session, user: NguoiDung, scan: LichSuScan, base_url: str) -> ScanOut:
    kq = json.loads(scan.ketQuaTho or "{}")
    mon = mon_an_repo.get_by_id(db, scan.idMonAn) if scan.idMonAn else None
    out: dict[str, Any] = {
        "idLichSuScan": scan.idLichSuScan,
        "duongDanAnh": _url(base_url, scan.duongDanAnh),
        "tenMonNhanDien": mon.tenMon if mon else (kq.get("tenMonThucTe") or ""),
        "doTinCay": float(scan.doTinCay) if scan.doTinCay is not None else None,
        "moTaNgan": kq.get("moTaNgan"),
        "laMonDacTrungHue": bool(kq.get("laMonDacTrungHue")),
        "idMonAn": scan.idMonAn,
    }
    if mon and mon.trangThai == TrangThaiNoiDung.ACTIVE.value:
        return ScanOut(
            **out, trangThai=TrangThaiScan.CO_TRONG_HE_THONG, monAn=mon_an_service.get_chi_tiet(db, mon.idMonAn, user)
        )
    ten_giong = {chuan_hoa_ten(t) for t in kq.get("monGanGiong") or [] if isinstance(t, str)}
    tuong_tu = [
        MonAnOut.model_validate(m)
        for m in mon_an_repo.list_active(db)
        if m.tenChuanHoa in ten_giong and m.idMonAn != scan.idMonAn
    ][:3]
    if mon is None:
        trang_thai = TrangThaiScan.KHONG_LUU
    elif _dang_cap_nhat(mon.idMonAn):
        trang_thai = TrangThaiScan.DANG_CAP_NHAT
    else:
        trang_thai = TrangThaiScan.CHUA_XAC_MINH
    if mon and mon.moTa and not out["moTaNgan"]:
        out["moTaNgan"] = mon.moTa
    return ScanOut(**out, trangThai=trang_thai, monTuongTu=tuong_tu)


def scan(
    db: Session, user: NguoiDung, noi_dung: bytes, base_url: str, background_tasks: BackgroundTasks
) -> ScanOut:
    dau_ngay = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if lich_su_scan_repo.dem_tu(db, user.idNguoiDung, dau_ngay) >= settings.SCAN_TOI_DA_MOI_NGAY:
        raise AppException(
            "SCAN_QUA_GIOI_HAN", f"Mỗi ngày chỉ được scan {settings.SCAN_TOI_DA_MOI_NGAY} ảnh, thử lại vào ngày mai", 429
        )
    duong_dan = luu_tru_service.luu_anh(noi_dung, "scan")  # kiểm tra định dạng/kích thước
    ds = mon_an_repo.list_chua_an(db)
    danh_muc = _ten_danh_muc(db)
    ten_mon = [m.tenMon for m in ds]
    kq = gemini_service.nhan_dien_anh(
        noi_dung, _MIME[duong_dan.rsplit(".", 1)[-1]], _prompt(ten_mon, danh_muc), _schema(ten_mon, danh_muc)
    )

    la_mon_an = bool(kq.get("laMonAn"))
    mon = _tim_mon(kq, ds) if la_mon_an else None
    if la_mon_an and mon is None and kq.get("laMonDacTrungHue") and (kq.get("tenMonThucTe") or "").strip():
        mon = _tao_mon(db, kq, danh_muc)
    if mon is not None and mon.trangThai == TrangThaiNoiDung.UNVERIFIED.value:
        _len_lich_lam_giau(background_tasks, mon)

    try:
        do_tin_cay = min(max(float(kq.get("doTinCay")), 0.0), 1.0)
    except (TypeError, ValueError):
        do_tin_cay = None
    scan_moi = lich_su_scan_repo.create(
        db,
        idNguoiDung=user.idNguoiDung,
        idMonAn=mon.idMonAn if mon else None,
        duongDanAnh=duong_dan,
        doTinCay=do_tin_cay,
        ketQuaTho=json.dumps(kq, ensure_ascii=False),
        ngayTao=datetime.now(),  # đặt từ Python để đếm lượt theo ngày đúng múi giờ
    )
    db.commit()
    if not la_mon_an:
        raise AppException("KHONG_NHAN_DIEN_DUOC", "Không nhận ra món ăn trong ảnh, hãy chụp rõ hơn", 422)
    return _ket_qua(db, user, scan_moi, base_url)


def get_ket_qua(db: Session, user: NguoiDung, id_scan: uuid.UUID, base_url: str) -> ScanOut:
    scan_ = lich_su_scan_repo.get_by_id(db, id_scan)
    if scan_ is None or scan_.idNguoiDung != user.idNguoiDung:
        raise NotFoundError("Không tìm thấy lượt scan", "SCAN_NOT_FOUND")
    if not json.loads(scan_.ketQuaTho or "{}").get("laMonAn"):
        raise AppException("KHONG_NHAN_DIEN_DUOC", "Không nhận ra món ăn trong ảnh, hãy chụp rõ hơn", 422)
    return _ket_qua(db, user, scan_, base_url)


def lich_su(db: Session, user: NguoiDung, page: int, size: int, base_url: str) -> Page[LichSuScanOut]:
    items, total = lich_su_scan_repo.list_cua_user(db, user.idNguoiDung, page, size)
    ten_mon = {m.idMonAn: m.tenMon for m in mon_an_repo.list_chua_an(db)}
    out = []
    for s in items:
        kq = json.loads(s.ketQuaTho or "{}")
        out.append(
            LichSuScanOut(
                idLichSuScan=s.idLichSuScan,
                duongDanAnh=_url(base_url, s.duongDanAnh),
                tenMonNhanDien=ten_mon.get(s.idMonAn) or kq.get("tenMonThucTe"),
                doTinCay=float(s.doTinCay) if s.doTinCay is not None else None,
                idMonAn=s.idMonAn,
                ngayTao=s.ngayTao,
            )
        )
    return Page[LichSuScanOut](items=out, total=total, page=page, size=size)


def list_mon_khong_luu(db: Session) -> list[MonScanKhongLuuOut]:
    """Món người dùng scan nhưng không lưu (không đặc trưng Huế), gom theo tên, nhiều lượt nhất trước."""
    nhom: dict[str, dict[str, Any]] = {}
    for s in lich_su_scan_repo.list_khong_gan_mon(db):
        kq = json.loads(s.ketQuaTho or "{}")
        ten = (kq.get("tenMonThucTe") or "").strip()
        if not kq.get("laMonAn") or not chuan_hoa_ten(ten):
            continue
        g = nhom.setdefault(chuan_hoa_ten(ten), {"tenMon": ten, "soLanScan": 0, "nguoi": set(), "lanCuoi": s.ngayTao})
        g["soLanScan"] += 1
        g["nguoi"].add(s.idNguoiDung)
        g["lanCuoi"] = max(g["lanCuoi"], s.ngayTao)
    return sorted(
        (
            MonScanKhongLuuOut(tenMon=g["tenMon"], soLanScan=g["soLanScan"], soNguoiScan=len(g["nguoi"]), lanCuoi=g["lanCuoi"])
            for g in nhom.values()
        ),
        key=lambda x: (-x.soLanScan, x.tenMon),
    )
