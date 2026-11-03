"""Pipeline thu thập dữ liệu tự động: LLM -> Wikipedia -> LLM (tag) -> DB -> Serper (quán).

Chống trùng: unique DB (tenChuanHoa, maWikipedia, maGooglePlace, tên danh mục/tag) + upsert ở đây
+ gửi danh sách món đã có cho Gemini + khoá GET_LOCK để không có 2 lần chạy chồng nhau.
"""
import json
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.chuan_hoa import chuan_hoa_ten, do_tuong_dong
from app.core.config import settings
from app.core.constants import (
    CHE_DO_AN,
    DANH_MUC_MON,
    KIEU_MON,
    VI_MON,
    Buoi,
    LoaiSoThich,
    LoaiThuThap,
    ThoiTiet,
    TrangThaiNoiDung,
)
from app.core.exceptions import ExternalServiceError
from app.core.geo import haversine_km
from app.db.session import SessionLocal
from app.models.mon_an import MonAn
from app.models.dia_diem import DiaDiem
from app.repositories import (
    anh_repo,
    bao_cao_repo,
    che_do_an_repo,
    danh_muc_repo,
    dia_diem_repo,
    mon_an_repo,
    nguyen_lieu_repo,
    so_thich_repo,
)
from app.services import danh_gia_service, llm_service, serper_service, wikipedia_service

logger = logging.getLogger(__name__)

_TEN_KHOA = "huetaste_thu_thap"
_LO_TRICH_XUAT = 5
_NGUONG_TEN_KHOP = 0.8  # tiêu đề Wikipedia coi như đúng món
_NGUONG_TEN_GAN = 0.5  # tiêu đề gần giống: cần thêm bằng chứng trong nội dung
_DO_DAI_NGUON = 2500
_MA_CHUA_CAU_HINH = {"LLM_NOT_CONFIGURED", "SERPER_NOT_CONFIGURED"}
_DA_DU_ANH = 2  # món/quán đã có từ ngần này ảnh thì không tốn thêm lượt Serper Images

_STR = {"type": "STRING"}


def _mang_enum(values: tuple[str, ...] | list[str]) -> dict[str, Any]:
    return {"type": "ARRAY", "items": {"type": "STRING", "enum": list(values)}}


# enum danhMuc lấy theo danh mục hiện có trong DB (admin quản lý), xem _ten_danh_muc
def _schema_danh_sach(danh_muc: list[str]) -> dict[str, Any]:
    return {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "tenMon": _STR,
                "tenGoiKhac": {"type": "ARRAY", "items": _STR},
                "danhMuc": {"type": "STRING", "enum": danh_muc},
            },
            "required": ["tenMon", "danhMuc"],
        },
    }


def _schema_tag(danh_muc: list[str]) -> dict[str, Any]:
    return {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "tenMon": _STR,
                "moTa": _STR,
                "danhMuc": {"type": "STRING", "enum": danh_muc},
                "nguyenLieu": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {"ten": _STR, "nhom": _STR, "laThanhPhanChinh": {"type": "BOOLEAN"}},
                        "required": ["ten", "laThanhPhanChinh"],
                    },
                },
                "buoiPhuHop": _mang_enum([b.value for b in Buoi]),
                "thoiTietPhuHop": _mang_enum([t.value for t in ThoiTiet]),
                "giaThamKhaoTu": {"type": "NUMBER", "nullable": True},
                "giaThamKhaoDen": {"type": "NUMBER", "nullable": True},
                "vi": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "ten": {"type": "STRING", "enum": list(VI_MON)},
                            "trongSo": {"type": "NUMBER"},
                        },
                        "required": ["ten", "trongSo"],
                    },
                },
                "kieu": _mang_enum(KIEU_MON),
                "cheDoAn": _mang_enum(CHE_DO_AN),
            },
            "required": [
                "tenMon",
                "moTa",
                "danhMuc",
                "nguyenLieu",
                "buoiPhuHop",
                "thoiTietPhuHop",
                "vi",
                "kieu",
                "cheDoAn",
            ],
        },
    }


# ---------------------------------------------------------------- khoá chạy


@contextmanager
def khoa_thu_thap(db: Session, ten_khoa: str = _TEN_KHOA) -> Iterator[bool]:
    """True nếu giành được khoá. GET_LOCK gắn với connection nên giữ 1 connection riêng tới khi xong
    (Session có thể trả connection về pool sau mỗi commit)."""
    engine = db.get_bind()
    if engine.dialect.name != "mysql":
        yield True
        return
    with engine.connect() as conn:
        co_khoa = conn.scalar(text("SELECT GET_LOCK(:t, 0)"), {"t": ten_khoa}) == 1
        try:
            yield co_khoa
        finally:
            if co_khoa:
                conn.execute(text("SELECT RELEASE_LOCK(:t)"), {"t": ten_khoa})


# ---------------------------------------------------------------- món ăn


def _prompt_danh_sach(so_mon: int, da_co: list[str]) -> str:
    da_co_txt = ", ".join(da_co) if da_co else "(chưa có)"
    return (
        "Bạn là chuyên gia ẩm thực xứ Huế (Thừa Thiên Huế, Việt Nam).\n"
        f"Liệt kê tối đa {so_mon} món ăn đặc sản hoặc món phổ biến ở thành phố Huế: bún, bánh, "
        "cơm, cháo, chè, ăn vặt, món chay Huế.\n"
        "Mỗi món gồm: tenMon (tên tiếng Việt có dấu, phổ biến nhất), tenGoiKhac (tên gọi khác nếu có), "
        "danhMuc (chọn trong danh sách cho phép).\n"
        "Chỉ liệt kê món có thật, không bịa. KHÔNG lặp lại các món đã có sau đây: "
        f"{da_co_txt}"
    )


def _prompt_tag(lo: list[tuple[dict, dict | None]]) -> str:
    phan = []
    for i, (uv, nd) in enumerate(lo, 1):
        nguon = (nd or {}).get("extract", "")[:_DO_DAI_NGUON] or "(không có nguồn, dùng hiểu biết chung)"
        phan.append(f"### Món {i}: {uv['tenMon']}\nNguồn Wikipedia:\n{nguon}")
    return (
        "Dựa trên nguồn Wikipedia (ưu tiên) và hiểu biết về ẩm thực Huế, trả về thông tin cho TỪNG món "
        "dưới đây, đúng thứ tự, giữ nguyên tenMon.\n"
        "- moTa: 2-3 câu tiếng Việt, giới thiệu món.\n"
        "- nguyenLieu: nguyên liệu chính và phụ (nhom: thịt, hải sản, rau, tinh bột, gia vị...).\n"
        "- buoiPhuHop: buổi người Huế hay ăn (sang/trua/chieu/toi/khuya).\n"
        "- thoiTietPhuHop: nong (trời nóng), mat, lanh (se lạnh), mua (trời mưa).\n"
        "- giaThamKhaoTu/Den: giá 1 phần ở Huế, đơn vị VND; null nếu không rõ.\n"
        "- vi: các vị nổi bật, trongSo 0.1-1.0 thể hiện mức độ.\n"
        "- kieu: kiểu món. cheDoAn: chỉ chọn 'Ăn chay' nếu món hoàn toàn chay; 'Không hải sản' nếu "
        "không có tôm, cua, hến, cá...; 'Ít dầu mỡ', 'Ít đường' khi phù hợp.\n\n" + "\n\n".join(phan)
    )


def _xac_minh(uv: dict) -> tuple[dict | None, bool]:
    """(nội dung Wikipedia, khớp tiêu đề chắc chắn). (None, False) nếu không xác minh được."""
    cac_ten = [uv["tenMon"], *uv["tenGoiKhac"]]
    tot_nhat: tuple[float, dict] | None = None
    for tu_khoa in [*cac_ten, f"{uv['tenMon']} Huế"]:
        for hit in wikipedia_service.tim_trang(tu_khoa, 3):
            diem = max(do_tuong_dong(hit["title"], ten) for ten in cac_ten)
            if tot_nhat is None or diem > tot_nhat[0]:
                tot_nhat = (diem, hit)
        if tot_nhat and tot_nhat[0] >= _NGUONG_TEN_KHOP:
            break
    if tot_nhat is None or tot_nhat[0] < _NGUONG_TEN_GAN:
        return None, False
    nd = wikipedia_service.lay_noi_dung(tot_nhat[1]["pageid"])
    if nd is None:
        return None, False
    if tot_nhat[0] >= _NGUONG_TEN_KHOP:
        return nd, True
    # Tiêu đề chỉ gần giống (vd bài chung "Bún"): chấp nhận làm nguồn nếu bài nhắc tới món và Huế,
    # nhưng không gắn maWikipedia để không gộp nhầm nhiều món vào cùng 1 bài.
    van_ban = chuan_hoa_ten(nd["extract"])
    if "hue" in van_ban.split() and chuan_hoa_ten(uv["tenMon"]) in van_ban:
        return nd, False
    return None, False


def _trich_tag(lo: list[tuple[dict, dict | None]], danh_muc: list[str]) -> list[dict | None]:
    data = llm_service.generate_json(_prompt_tag(lo), _schema_tag(danh_muc), thu_tu=settings.LLM_THU_TU_TAG)
    if not isinstance(data, list):
        return [None] * len(lo)
    theo_ten = {chuan_hoa_ten(d.get("tenMon", "")): d for d in data if isinstance(d, dict)}
    ket_qua = []
    for i, (uv, _) in enumerate(lo):
        tag = theo_ten.get(chuan_hoa_ten(uv["tenMon"]))
        if tag is None and len(data) == len(lo) and isinstance(data[i], dict):
            tag = data[i]
        ket_qua.append(tag)
    return ket_qua


def _csv(values: Any, hop_le: set[str]) -> str | None:
    if not isinstance(values, list):
        return None
    chon = [v for v in dict.fromkeys(values) if v in hop_le]
    return ",".join(chon)[:50] or None


def _gia(v: Any) -> Decimal | None:
    try:
        return Decimal(int(float(v))) if v is not None and float(v) > 0 else None
    except (TypeError, ValueError):
        return None


def _cap_nhat_mon(db: Session, mon: MonAn, fields: dict[str, Any], id_danh_muc: Any) -> None:
    if mon.trangThai == TrangThaiNoiDung.ACTIVE.value and fields["trangThai"] != mon.trangThai:
        fields = {**fields, "trangThai": mon.trangThai}  # không hạ món đã xác minh về unverified
    page_id = fields.pop("maWikipedia")
    if page_id and mon.maWikipedia is None and mon_an_repo.get_by_wiki(db, page_id) is None:
        mon.maWikipedia = page_id
    for k, v in fields.items():
        if v is not None and k != "tenMon":
            setattr(mon, k, v)
    mon.idDanhMucMonAn = id_danh_muc


def _luu_tag(db: Session, mon: MonAn, tag: dict) -> None:
    nguyen_lieu = [
        (nguyen_lieu_repo.get_or_create(db, x["ten"][:150], (x.get("nhom") or None)).idNguyenLieu,
         bool(x.get("laThanhPhanChinh")))
        for x in tag.get("nguyenLieu", [])
        if isinstance(x, dict) and (x.get("ten") or "").strip()
    ]
    mon_an_repo.replace_nguyen_lieu(db, mon.idMonAn, nguyen_lieu)

    so_thich = [
        (so_thich_repo.get_or_create(db, LoaiSoThich.VI.value, v["ten"]).idSoThich,
         round(min(max(float(v.get("trongSo", 1)), 0.1), 1.0), 2))
        for v in tag.get("vi", [])
        if isinstance(v, dict) and v.get("ten") in VI_MON
    ] + [
        (so_thich_repo.get_or_create(db, LoaiSoThich.KIEU.value, k).idSoThich, 1.0)
        for k in tag.get("kieu", [])
        if k in KIEU_MON
    ]
    mon_an_repo.replace_so_thich(db, mon.idMonAn, so_thich)

    che_do = [che_do_an_repo.get_or_create(db, c).idCheDoAn for c in tag.get("cheDoAn", []) if c in CHE_DO_AN]
    mon_an_repo.replace_che_do_an(db, mon.idMonAn, che_do)


def _khoa_ten(uv: dict) -> list[str]:
    return list(dict.fromkeys(k for k in (chuan_hoa_ten(t) for t in [uv["tenMon"], *uv["tenGoiKhac"]]) if k))


def _tim_mon(db: Session, keys: list[str], nd: dict | None) -> MonAn | None:
    # Tra theo pageid kể cả khi chỉ khớp gần đúng: bài đó đã là nguồn của một món -> cùng món
    # (vd "Bún bò" -> bài "Bún bò Huế"). Chỉ GHI maWikipedia khi khớp chắc (page_id).
    theo_wiki = mon_an_repo.get_by_wiki(db, nd["pageid"]) if nd else None
    return theo_wiki or mon_an_repo.get_by_ten_chuan_hoa(db, keys)


def _luu_mon(
    db: Session, uv: dict, nd: dict | None, khop_chac: bool, tag: dict | None, danh_muc: list[str]
) -> str:
    """Upsert 1 món. Trả 'moi' hoặc 'capNhat'."""
    tag = tag or {}
    keys = _khoa_ten(uv)
    page_id = nd["pageid"] if nd and khop_chac else None
    fields: dict[str, Any] = {
        "tenMon": uv["tenMon"][:255],
        "moTa": tag.get("moTa") or ((nd or {}).get("extract") or "")[:1000] or None,
        "hinhAnh": (nd or {}).get("anh"),
        "buoiPhuHop": _csv(tag.get("buoiPhuHop"), {b.value for b in Buoi}),
        "thoiTietPhuHop": _csv(tag.get("thoiTietPhuHop"), {t.value for t in ThoiTiet}),
        "giaThamKhaoTu": _gia(tag.get("giaThamKhaoTu")),
        "giaThamKhaoDen": _gia(tag.get("giaThamKhaoDen")),
        "trangThai": (TrangThaiNoiDung.ACTIVE if nd else TrangThaiNoiDung.UNVERIFIED).value,
        "maWikipedia": page_id,
        "nguonThamKhao": (nd or {}).get("url"),
    }
    ten_danh_muc = tag.get("danhMuc") if tag.get("danhMuc") in danh_muc else uv["danhMuc"]
    dm = danh_muc_repo.get_or_create(db, ten_danh_muc if ten_danh_muc in danh_muc else "Món mặn khác")

    def _tim() -> MonAn | None:
        return _tim_mon(db, keys, nd)

    mon = _tim()
    la_moi = mon is None
    try:
        with db.begin_nested():
            if mon is None:
                mon = mon_an_repo.create(
                    db, idDanhMucMonAn=dm.idDanhMucMonAn, tenChuanHoa=keys[0], **fields
                )
            else:
                _cap_nhat_mon(db, mon, dict(fields), dm.idDanhMucMonAn)
                db.flush()
    except IntegrityError:
        # unique chặn: bản ghi trùng đã tồn tại -> chuyển sang cập nhật bản đó
        mon = _tim()
        if mon is None:
            raise
        la_moi = False
        _cap_nhat_mon(db, mon, dict(fields), dm.idDanhMucMonAn)
    if tag:
        _luu_tag(db, mon, tag)
    return "moi" if la_moi else "capNhat"


def _ten_danh_muc(db: Session) -> list[str]:
    """Danh mục admin đang quản lý; DB trống thì dùng bộ mặc định DANH_MUC_MON."""
    return [d.tenDanhMuc for d in danh_muc_repo.list_all(db)] or list(DANH_MUC_MON)


def thu_thap_mon_an(db: Session, so_mon: int) -> dict[str, int]:
    da_co = mon_an_repo.list_ten(db)
    da_co_khoa = mon_an_repo.list_ten_chuan_hoa(db)
    danh_muc = _ten_danh_muc(db)
    ds = llm_service.generate_json(
        _prompt_danh_sach(so_mon, da_co),
        _schema_danh_sach(danh_muc),
        temperature=0.4,
        thu_tu=settings.LLM_THU_TU_DANH_SACH,
    )

    ung_vien: list[dict] = []
    da_gap = set(da_co_khoa)
    for uv in ds if isinstance(ds, list) else []:
        ten = (uv.get("tenMon") or "").strip() if isinstance(uv, dict) else ""
        khoa = chuan_hoa_ten(ten)
        if not khoa or khoa in da_gap:
            continue  # Gemini lặp món đã có / lặp trong cùng danh sách
        da_gap.add(khoa)
        ung_vien.append(
            {
                "tenMon": ten,
                "tenGoiKhac": [t.strip() for t in uv.get("tenGoiKhac") or [] if isinstance(t, str) and t.strip()],
                "danhMuc": uv.get("danhMuc"),
            }
        )
        if len(ung_vien) >= so_mon:
            break
    return _xu_ly_ung_vien(db, ung_vien, danh_muc)


def _xu_ly_ung_vien(db: Session, ung_vien: list[dict], danh_muc: list[str]) -> dict[str, int]:
    """Xác minh Wikipedia -> trích tag theo lô -> upsert. Dùng chung cho thu thập định kỳ và món từ scan."""
    thong_ke = {"deXuat": len(ung_vien), "moi": 0, "capNhat": 0, "chuaXacMinh": 0, "loi": 0, "anhMon": 0}
    for i in range(0, len(ung_vien), _LO_TRICH_XUAT):
        lo: list[tuple[dict, dict | None, bool]] = []
        for uv in ung_vien[i : i + _LO_TRICH_XUAT]:
            try:
                nd, khop_chac = _xac_minh(uv)
            except ExternalServiceError as e:
                logger.warning("Không xác minh được '%s': %s", uv["tenMon"], e.message)
                nd, khop_chac = None, False
            lo.append((uv, nd, khop_chac))
        try:
            tags = _trich_tag([(uv, nd) for uv, nd, _ in lo], danh_muc)
        except ExternalServiceError as e:
            if e.code in _MA_CHUA_CAU_HINH:
                raise
            logger.warning("Gemini lỗi khi trích tag: %s", e.message)
            tags = [None] * len(lo)
        for (uv, nd, khop_chac), tag in zip(lo, tags):
            try:
                with db.begin_nested():
                    thong_ke[_luu_mon(db, uv, nd, khop_chac, tag, danh_muc)] += 1
                if nd is None:
                    thong_ke["chuaXacMinh"] += 1
            except Exception:
                logger.exception("Lỗi khi lưu món '%s'", uv["tenMon"])
                thong_ke["loi"] += 1
            else:
                mon = _tim_mon(db, _khoa_ten(uv), nd)
                if mon is not None:
                    thong_ke["anhMon"] += _luu_anh_mon_an_toan(db, mon)
        db.commit()
        logger.info("Món ăn: đã xử lý %s/%s", min(i + _LO_TRICH_XUAT, len(ung_vien)), len(ung_vien))
    return thong_ke


# ---------------------------------------------------------------- ảnh (Serper Images)


def _tu_khoa_mon(mon: MonAn) -> str:
    return mon.tenMon if chuan_hoa_ten(mon.tenMon).endswith(" hue") else f"{mon.tenMon} Huế"


def _them_anh(ds: list[dict[str, Any]], ten: str, can: int, them: Callable[[dict[str, Any]], bool]) -> int:
    """Thêm tối đa `can` ảnh hợp lệ: URL http(s), đủ rộng, tiêu đề ảnh nhắc đến `ten` (tránh ảnh lạc đề)."""
    them_duoc = 0
    for a in ds:
        if them_duoc >= can:
            break
        url = a.get("url") or ""
        rong = a.get("rong")
        if not url.startswith(("http://", "https://")):
            continue
        if rong is not None and rong < settings.THU_THAP_ANH_RONG_TOI_THIEU:
            continue
        if not ten_mon_trong_ten_quan(ten, a.get("tieuDe") or ""):
            continue
        if them(a):
            them_duoc += 1
    return them_duoc


def _luu_anh_mon(db: Session, mon: MonAn) -> int:
    """1 lượt Serper Images cho món `active` còn thiếu ảnh. Trả số ảnh mới thêm."""
    toi_da = settings.THU_THAP_SO_ANH_MON
    da_co = anh_repo.dem_mon(db, mon.idMonAn)
    if not settings.THU_THAP_ANH_BAT or mon.trangThai != TrangThaiNoiDung.ACTIVE.value:
        return 0
    if da_co >= min(toi_da, _DA_DU_ANH):
        return 0
    ds = serper_service.tim_anh(f"{_tu_khoa_mon(mon)} món ăn", toi_da * 3)
    them_duoc = _them_anh(ds, mon.tenMon, toi_da - da_co, lambda a: anh_repo.them_mon(db, mon.idMonAn, a))
    if them_duoc and not mon.hinhAnh:
        mon.hinhAnh = anh_repo.list_mon(db, mon.idMonAn)[0].url
    return them_duoc


def _luu_anh_quan(db: Session, dd: DiaDiem, anh_maps: str | None) -> int:
    """Thumbnail Maps (nếu có) + 1 lượt Serper Images cho quán còn thiếu ảnh. Trả số ảnh mới thêm."""
    if not settings.THU_THAP_ANH_BAT:
        return 0
    toi_da = settings.THU_THAP_SO_ANH_QUAN
    them_duoc = 0
    if anh_maps and anh_repo.them_dia_diem(db, dd.idDiaDiem, {"url": anh_maps, "nguon": "Google Maps"}):
        them_duoc += 1
    da_co = anh_repo.dem_dia_diem(db, dd.idDiaDiem)
    if da_co < min(toi_da, _DA_DU_ANH):
        ds = serper_service.tim_anh(f"{dd.tenDiaDiem} {dd.diaChi or 'Huế'}", toi_da * 3)
        them_duoc += _them_anh(
            ds, dd.tenDiaDiem, toi_da - da_co, lambda a: anh_repo.them_dia_diem(db, dd.idDiaDiem, a)
        )
    if them_duoc and not dd.hinhAnh:
        dd.hinhAnh = anh_repo.list_dia_diem(db, dd.idDiaDiem)[0].url
    return them_duoc


def _luu_anh_mon_an_toan(db: Session, mon: MonAn) -> int:
    """Lỗi ảnh không được làm hỏng việc lưu món: chỉ ghi log."""
    try:
        with db.begin_nested():
            return _luu_anh_mon(db, mon)
    except ExternalServiceError as e:
        logger.warning("Tìm ảnh lỗi với món '%s': %s", mon.tenMon, e.message)
    except Exception:
        logger.exception("Lỗi khi lưu ảnh món '%s'", mon.tenMon)
    return 0


def _luu_anh_quan_an_toan(db: Session, dd: DiaDiem, anh_maps: str | None) -> int:
    try:
        with db.begin_nested():
            return _luu_anh_quan(db, dd, anh_maps)
    except ExternalServiceError as e:
        logger.warning("Tìm ảnh lỗi với quán '%s': %s", dd.tenDiaDiem, e.message)
    except Exception:
        logger.exception("Lỗi khi lưu ảnh quán '%s'", dd.tenDiaDiem)
    return 0


# ---------------------------------------------------------------- địa điểm


def ten_mon_trong_ten_quan(ten_mon: str, ten_quan: str) -> bool:
    """Quán mang tên món ("Bánh canh Nam Phổ Bà Đợi"). Bỏ đuôi "Huế" của tên món khi còn ≥ 2 từ
    ("Bánh ép Huế" khớp "Bánh ép Bà Đỏ", nhưng "Chè Huế" không bị rút thành "chè" khớp mọi quán chè)."""
    quan = f" {chuan_hoa_ten(ten_quan)} "
    khoa = chuan_hoa_ten(ten_mon)
    cac_khoa = [khoa]
    if khoa.endswith(" hue") and len(khoa.removesuffix(" hue").split()) >= 2:
        cac_khoa.append(khoa.removesuffix(" hue"))
    return any(k and f" {k} " in quan for k in cac_khoa)


def _luu_quan(db: Session, mon: MonAn, p: dict[str, Any], ban_kinh_km: float) -> str | None:
    """`p` là kết quả đã chuẩn hoá bởi serper_service.chuan_hoa."""
    vi_do, kinh_do = p.get("viDo"), p.get("kinhDo")
    if not p.get("id") or vi_do is None or kinh_do is None:
        return None
    if haversine_km(settings.HUE_VI_DO, settings.HUE_KINH_DO, vi_do, kinh_do) > ban_kinh_km:
        return None  # tìm theo vị trí chỉ là ưu tiên, vẫn có thể trả quán ngoài Huế
    ten = (p.get("ten") or "Không rõ tên")[:255]
    gio = p.get("gioMoCua")
    fields: dict[str, Any] = {
        "tenDiaDiem": ten,
        "diaChi": p.get("diaChi"),
        "viDo": Decimal(str(round(vi_do, 7))),
        "kinhDo": Decimal(str(round(kinh_do, 7))),
        "soDienThoai": (p.get("soDienThoai") or "")[:20] or None,
        "gioMoCua": json.dumps(gio, ensure_ascii=False) if gio else None,
        "mucGia": p.get("mucGia"),
        "diemGoogle": Decimal(str(round(p["rating"], 2))) if p.get("rating") is not None else None,
        "soDanhGiaGoogle": int(p["soDanhGia"]) if p.get("soDanhGia") else None,
        "hinhAnh": p.get("anh"),
    }
    dd = dia_diem_repo.get_by_place_id(db, p["id"])
    if dd is None:
        dd = dia_diem_repo.create(
            db, maGooglePlace=p["id"], trangThai=TrangThaiNoiDung.ACTIVE.value, **fields
        )
        ket_qua = "quanMoi"
    else:
        for k, v in fields.items():
            if v is not None:
                setattr(dd, k, v)
        ket_qua = "quanCapNhat"
    danh_gia_service.tinh_lai_diem_quan(db, dd)  # gộp rating Google mới với đánh giá trong app
    dac_trung = ten_mon_trong_ten_quan(mon.tenMon, ten)
    if not bao_cao_repo.mon_bi_go(db, mon.idMonAn, dd.idDiaDiem):  # admin đã gỡ qua báo cáo vi phạm
        dia_diem_repo.link_mon(db, mon.idMonAn, dd.idDiaDiem, dac_trung)
    return ket_qua


def _thong_ke_quan() -> dict[str, int]:
    return {
        "monDaXet": 0, "quanMoi": 0, "quanCapNhat": 0, "lienKet": 0, "monXacMinh": 0, "loi": 0,
        "anhMon": 0, "anhQuan": 0,
    }


def thu_thap_dia_diem(db: Session, so_quan_moi_mon: int) -> dict[str, int]:
    thong_ke = _thong_ke_quan()
    ban_kinh = settings.HUE_BAN_KINH_KM
    # Xét cả món unverified: món Huế ít tài liệu không có bài Wikipedia, nhưng Google Maps có quán
    # ở Huế mang tên món là bằng chứng món có thật -> chuyển active (cùng quy tắc với món từ scan)
    for mon in mon_an_repo.list_chua_an(db):
        co_quan = _tim_quan_cho_mon(db, mon, so_quan_moi_mon, ban_kinh, thong_ke)
        if mon.trangThai == TrangThaiNoiDung.UNVERIFIED.value and co_quan:
            mon.trangThai = TrangThaiNoiDung.ACTIVE.value
            thong_ke["monXacMinh"] += 1
            logger.info("Món '%s' được xác minh nhờ quán mang tên món trên Google Maps", mon.tenMon)
        thong_ke["anhMon"] += _luu_anh_mon_an_toan(db, mon)
        db.commit()
    return thong_ke


def _tim_quan_cho_mon(
    db: Session, mon: MonAn, so_quan: int, ban_kinh: float, thong_ke: dict[str, int]
) -> bool:
    """1 lượt Serper cho 1 món. Trả True nếu có ít nhất 1 quán mang tên món (laMonDacTrung)."""
    try:
        places = serper_service.tim_quan(_tu_khoa_mon(mon), settings.HUE_VI_DO, settings.HUE_KINH_DO, so_quan)
    except ExternalServiceError as e:
        if e.code in _MA_CHUA_CAU_HINH:
            raise
        logger.warning("Tìm quán lỗi với '%s': %s", mon.tenMon, e.message)
        thong_ke["loi"] += 1
        return False
    thong_ke["monDaXet"] += 1
    co_quan_dac_trung = False
    for p in places[:so_quan]:
        try:
            with db.begin_nested():
                kq = _luu_quan(db, mon, p, ban_kinh)
            if kq:
                thong_ke[kq] += 1
                thong_ke["lienKet"] += 1
                co_quan_dac_trung |= ten_mon_trong_ten_quan(mon.tenMon, p.get("ten") or "")
            if kq and (dd := dia_diem_repo.get_by_place_id(db, p["id"])) is not None:
                thong_ke["anhQuan"] += _luu_anh_quan_an_toan(db, dd, p.get("anh"))
        except Exception:
            logger.exception("Lỗi khi lưu quán cho '%s'", mon.tenMon)
            thong_ke["loi"] += 1
    return co_quan_dac_trung


# ---------------------------------------------------------------- điểm vào chung


def chay(
    loai: LoaiThuThap,
    so_mon: int | None = None,
    session_factory: Callable[[], Session] = SessionLocal,
) -> dict[str, Any] | None:
    """Dùng chung cho worker, CLI và endpoint admin. None nếu đang có lần chạy khác giữ khoá."""
    with session_factory() as db, khoa_thu_thap(db) as co_khoa:
        if not co_khoa:
            logger.warning("Đang có tiến trình thu thập khác chạy, bỏ qua lần này")
            return None
        ket_qua: dict[str, Any] = {}
        try:
            if loai in (LoaiThuThap.MON_AN, LoaiThuThap.TAT_CA):
                ket_qua["monAn"] = thu_thap_mon_an(db, so_mon or settings.THU_THAP_SO_MON)
            if loai in (LoaiThuThap.DIA_DIEM, LoaiThuThap.TAT_CA):
                ket_qua["diaDiem"] = thu_thap_dia_diem(db, settings.THU_THAP_QUAN_MOI_MON)
        except ExternalServiceError as e:
            db.rollback()
            logger.error("Dừng thu thập: %s", e.message)
            ket_qua["loi"] = e.message
        logger.info("Kết quả thu thập: %s", ket_qua)
        return ket_qua


# ---------------------------------------------------------------- món mới từ scan ảnh


def lam_giau_mon(id_mon: Any, session_factory: Callable[[], Session] | None = None) -> None:
    """Chạy nền sau POST /scan: tìm hiểu 1 món Huế người dùng vừa scan (Wikipedia, tag, quán).

    Món đang `unverified` chỉ thành `active` khi Wikipedia xác minh được HOẶC Serper có quán ở Huế
    mang tên món, vì câu "đặc trưng Huế" của model vision có thể sai. Lỗi chỉ ghi log.
    """
    with (session_factory or SessionLocal)() as db:
        mon = mon_an_repo.get_by_id(db, id_mon)
        if mon is None or mon.trangThai != TrangThaiNoiDung.UNVERIFIED.value:
            return
        # khoá riêng từng món (không dùng khoá chung: job hằng tháng giữ rất lâu); GET_LOCK tối đa 64 ký tự
        with khoa_thu_thap(db, f"huetaste_mon_{mon.tenChuanHoa}"[:64]) as co_khoa:
            if not co_khoa:
                logger.info("Món '%s' đang được làm giàu ở tiến trình khác", mon.tenMon)
                return
            try:
                ten_dm = danh_muc_repo.get_by_id(db, mon.idDanhMucMonAn)
                uv = {"tenMon": mon.tenMon, "tenGoiKhac": [], "danhMuc": ten_dm.tenDanhMuc if ten_dm else None}
                _xu_ly_ung_vien(db, [uv], _ten_danh_muc(db))
                db.refresh(mon)
                thong_ke = _thong_ke_quan()
                co_quan = _tim_quan_cho_mon(
                    db, mon, settings.THU_THAP_QUAN_MOI_MON, settings.HUE_BAN_KINH_KM, thong_ke
                )
                if mon.trangThai == TrangThaiNoiDung.UNVERIFIED.value and co_quan:
                    mon.trangThai = TrangThaiNoiDung.ACTIVE.value
                thong_ke["anhMon"] += _luu_anh_mon_an_toan(db, mon)
                db.commit()
                logger.info("Làm giàu món scan '%s': %s, quán %s", mon.tenMon, mon.trangThai, thong_ke)
            except Exception:
                db.rollback()
                logger.exception("Lỗi khi làm giàu món scan '%s'", mon.tenMon)
