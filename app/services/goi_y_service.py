"""Gợi ý món ăn / địa điểm theo ngữ cảnh: content-based + luật ngữ cảnh, chấm điểm có trọng số.

Điểm món = 0.30 ngữ cảnh + 0.30 sở thích + 0.15 ngân sách + 0.15 đánh giá + 0.10 ghi chú/yêu thích.
Điểm quán = 0.35 món tốt nhất + 0.25 khoảng cách + 0.20 rating + 0.10 ngân sách + 0.10 món đặc trưng.
Mỗi thành phần 0..1 và sinh câu lý do -> GoiY.lyDoGiaiThich. Các hàm cham_* là hàm thuần (test không cần DB).
"""
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.chuan_hoa import chuan_hoa_ten
from app.core.constants import BUA_AN_VAT, CHE_DO_CHAY, TEN_BUOI, Buoi, LoaiGoiY, LoaiSoThich
from app.models.dia_diem import DiaDiem
from app.models.mon_an import MonAn
from app.models.mon_an_dia_diem import MonAnDiaDiem
from app.models.nguoi_dung import NguoiDung
from app.repositories import che_do_an_repo, dia_diem_repo, goi_y_repo, mon_an_repo, so_thich_repo
from app.schemas.goi_y import DiaDiemGoiYOut, KetQuaGoiYOut, MonGoiYOut, NguCanhOut, YeuCauGoiY
from app.schemas.mon_an import MonAnOut
from app.services import ngu_canh_service
from app.services.dia_diem_service import dia_diem_out, khoang_cach

TRONG_SO_MON = {"nguCanh": 0.30, "soThich": 0.30, "nganSach": 0.15, "danhGia": 0.15, "ghiChu": 0.10}
TRONG_SO_QUAN = {"mon": 0.35, "khoangCach": 0.25, "rating": 0.20, "nganSach": 0.10, "dacTrung": 0.10}
TOI_DA_MOI_DANH_MUC = 2
SO_MON_XET_QUAN = 20
BAN_KINH_CHAM_KM = 5.0  # quán xa hơn mức này điểm khoảng cách = 0
# DiaDiem.mucGia (1..4) -> giá ước lượng 1 người khi quán không ghi giá món
GIA_THEO_MUC = {1: 30_000, 2: 60_000, 3: 150_000, 4: 300_000}

_TEN_THOI_TIET = {"lanh": "se lạnh", "mua": "mưa", "nong": "nóng", "mat": "mát mẻ"}
_KIEU_AN_VAT = {"Ăn vặt", "Chè - tráng miệng", "Bánh"}
# (cụm từ không dấu trong ghi chú, tag, dấu): cụm phủ định đặt trước để "it cay" không bị đếm là "cay"
_TU_KHOA_GHI_CHU: tuple[tuple[str, str, int], ...] = (
    ("khong an cay", "Cay", -1),
    ("khong cay", "Cay", -1),
    ("it cay", "Cay", -1),
    ("it beo", "Béo", -1),
    ("it dau mo", "Béo", -1),
    ("it ngot", "Ngọt", -1),
    ("cay", "Cay", 1),
    ("nuoc dung", "Món nước", 1),
    ("am nong", "Món nước", 1),
    ("nong hoi", "Món nước", 1),
    ("nhieu rau", "Thanh đạm", 1),
    ("an nhe", "Thanh đạm", 1),
    ("thanh dam", "Thanh đạm", 1),
    ("dam da", "Đậm đà", 1),
    ("ngot", "Ngọt", 1),
    ("chua", "Chua", 1),
    ("beo", "Béo", 1),
)


@dataclass
class DuLieuMon:
    mon: MonAn
    buoi: set[str]
    thoi_tiet: set[str]
    gia: float | None
    tags: dict[uuid.UUID, tuple[str, str, float]]  # idSoThich -> (loai, ten, trongSo)
    che_do: set[uuid.UUID]
    danh_gia: float | None  # thang 5
    la_chay: bool
    la_yeu_thich: bool

    def co_tag(self, ten: str) -> float | None:
        for _, t, w in self.tags.values():
            if t == ten:
                return w
        return None


@dataclass
class NguCanhCham:
    buoi: str
    bua_an: str | None
    thoi_tiet: str | None
    nhiet_do: float | None
    la_ngay_ram: bool
    ngan_sach: int | None
    ghi_chu: str | None
    so_thich: dict[uuid.UUID, int]  # idSoThich -> mucDo 1..5


@dataclass
class DiemMon:
    du_lieu: DuLieuMon
    tong: float
    thanh_phan: dict[str, float]
    ly_do: list[tuple[float, str]] = field(default_factory=list)  # (đóng góp, câu)


@dataclass
class DiemQuan:
    dd: DiaDiem
    tong: float
    khoang_cach_km: float | None
    mon: list[DiemMon]
    ly_do: list[str]


# ---------------------------------------------------------------- chấm điểm món


def _vnd(n: float) -> str:
    return f"{int(n):,}".replace(",", ".") + "đ"


def cham_ngu_canh(m: DuLieuMon, nc: NguCanhCham) -> tuple[float, list[str]]:
    ly_do: list[str] = []
    if m.buoi:
        diem_buoi = 1.0 if nc.buoi in m.buoi else 0.2
        if diem_buoi == 1.0:
            ly_do.append(f"Hợp {TEN_BUOI.get(Buoi(nc.buoi), nc.buoi)}")
    else:
        diem_buoi = 0.5
    if nc.thoi_tiet and m.thoi_tiet:
        diem_tt = 1.0 if nc.thoi_tiet in m.thoi_tiet else 0.3
        if diem_tt == 1.0:
            nhiet = f" {nc.nhiet_do:.0f}°C" if nc.nhiet_do is not None else ""
            ly_do.append(f"Trời {_TEN_THOI_TIET.get(nc.thoi_tiet, nc.thoi_tiet)}{nhiet} rất hợp")
    else:
        diem_tt = 0.5
    diem = 0.5 * diem_buoi + 0.5 * diem_tt

    if nc.bua_an == BUA_AN_VAT and any(t in _KIEU_AN_VAT for _, t, _ in m.tags.values()):
        diem = min(1.0, diem + 0.3)
        ly_do.append("Hợp để ăn vặt")
    if nc.la_ngay_ram:
        if m.la_chay:
            diem = min(1.0, diem + 0.5)
            ly_do.insert(0, "Hôm nay mùng 1/rằm âm lịch, món chay thanh tịnh")
        else:
            diem *= 0.6
    return diem, ly_do


def cham_so_thich(m: DuLieuMon, nc: NguCanhCham) -> tuple[float, list[str]]:
    if not nc.so_thich:
        return 0.5, []
    khop = sorted(
        ((m.tags[i][2] * muc / 5, m.tags[i]) for i, muc in nc.so_thich.items() if i in m.tags),
        key=lambda x: -x[0],
    )
    if not khop:
        return 0.1, []
    # noisy-OR: một sở thích khớp mạnh đã đủ điểm cao, khớp thêm thì tăng dần tới 1
    con_lai = 1.0
    for v, _ in khop:
        con_lai *= 1 - v
    loai, ten, _ = khop[0][1]
    cau = f"Đúng khẩu vị {ten.lower()} bạn thích" if loai == LoaiSoThich.VI.value else f"Đúng kiểu {ten.lower()} bạn thích"
    return 1 - con_lai, [cau]


def cham_ngan_sach(gia: float | None, ngan_sach: int | None) -> tuple[float, list[str]]:
    if not ngan_sach or gia is None:
        return 0.5, []
    if gia <= ngan_sach:
        return 1.0, [f"Trong ngân sách {_vnd(ngan_sach)}"]
    if gia >= 1.5 * ngan_sach:
        return 0.0, []
    return 1 - (gia - ngan_sach) / (0.5 * ngan_sach), []


def cham_danh_gia(danh_gia: float | None) -> tuple[float, list[str]]:
    if danh_gia is None:
        return 0.5, []
    return min(danh_gia / 5, 1.0), [f"Được đánh giá {danh_gia:.1f}★"] if danh_gia >= 4.5 else []


def cham_ghi_chu(m: DuLieuMon, ghi_chu: str | None) -> tuple[float, list[str]]:
    diem, ly_do = 0.5, []
    if ghi_chu:
        van_ban = f" {chuan_hoa_ten(ghi_chu)} "
        da_tinh: set[str] = set()
        for cum, tag, dau in _TU_KHOA_GHI_CHU:
            if f" {cum} " not in van_ban:
                continue
            van_ban = van_ban.replace(f" {cum} ", " ")
            if tag in da_tinh:  # "nước dùng" + "ấm nóng" cùng là Món nước: chỉ tính 1 lần
                continue
            da_tinh.add(tag)
            w = m.co_tag(tag)
            if dau > 0:
                diem += 0.25 * w if w else -0.1
                if w:
                    ly_do.append(f"Đúng ý bạn: {tag.lower()}")
            elif w:
                diem -= 0.3 * w
        if " chay " in van_ban:
            diem += 0.4 if m.la_chay else -0.3
    if m.la_yeu_thich:
        diem += 0.3
        ly_do.append("Món bạn đã yêu thích")
    return min(max(diem, 0.0), 1.0), ly_do


def cham_diem_mon(m: DuLieuMon, nc: NguCanhCham) -> DiemMon:
    ket_qua = {
        "nguCanh": cham_ngu_canh(m, nc),
        "soThich": cham_so_thich(m, nc),
        "nganSach": cham_ngan_sach(m.gia, nc.ngan_sach),
        "danhGia": cham_danh_gia(m.danh_gia),
        "ghiChu": cham_ghi_chu(m, nc.ghi_chu),
    }
    thanh_phan = {k: v[0] for k, v in ket_qua.items()}
    tong = sum(TRONG_SO_MON[k] * v for k, v in thanh_phan.items())
    ly_do = [(TRONG_SO_MON[k] * thanh_phan[k], cau) for k, (_, caus) in ket_qua.items() for cau in caus]
    return DiemMon(m, round(tong, 4), thanh_phan, ly_do)


def loc_che_do_an(ds: list[DuLieuMon], che_do_nguoi_dung: set[uuid.UUID]) -> list[DuLieuMon]:
    """Lọc cứng: món phải phù hợp MỌI chế độ ăn người dùng chọn (vd Ăn chay thì loại món mặn)."""
    return [m for m in ds if che_do_nguoi_dung <= m.che_do]


def loc_nguyen_lieu_tranh(ds: list[DuLieuMon], ids_mon_bi_loai: set[uuid.UUID]) -> list[DuLieuMon]:
    """Lọc cứng: bỏ món chứa nguyên liệu người dùng cần tránh."""
    return [m for m in ds if m.mon.idMonAn not in ids_mon_bi_loai]


def chon_top_mon(ds: list[DiemMon], so_mon: int) -> list[DiemMon]:
    """Sắp xếp theo điểm, mỗi danh mục tối đa TOI_DA_MOI_DANH_MUC món để kết quả đa dạng."""
    xep = sorted(ds, key=lambda d: (-d.tong, d.du_lieu.mon.tenMon))
    chon, du, dem = [], [], defaultdict(int)
    for d in xep:
        dm = d.du_lieu.mon.idDanhMucMonAn
        if dem[dm] < TOI_DA_MOI_DANH_MUC:
            chon.append(d)
            dem[dm] += 1
        else:
            du.append(d)
    return (chon + du)[:so_mon] if len(chon) < so_mon else chon[:so_mon]


def ly_do_mon(d: DiemMon) -> str:
    # 3 câu có đóng góp điểm lớn nhất, bỏ trùng
    caus = [c for _, c in sorted(d.ly_do, key=lambda x: -x[0])]
    return " · ".join(list(dict.fromkeys(caus))[:3]) or "Đặc sản Huế được nhiều người yêu thích"


# ---------------------------------------------------------------- chấm điểm quán


def cham_diem_quan(
    dd: DiaDiem, cac_mon: list[tuple[DiemMon, MonAnDiaDiem]], kc: float | None, ngan_sach: int | None
) -> DiemQuan:
    cac_mon = sorted(cac_mon, key=lambda x: -x[0].tong)
    tot_nhat, link = cac_mon[0]
    diem_kc = 0.5 if kc is None else max(0.0, 1 - kc / BAN_KINH_CHAM_KM)
    rating = float(dd.diemTrungBinh) if dd.diemTrungBinh is not None else None
    diem_rating = rating / 5 if rating is not None else 0.5
    gia = float(link.giaBan) if link.giaBan is not None else GIA_THEO_MUC.get(dd.mucGia or 0)
    diem_gia, _ = cham_ngan_sach(gia, ngan_sach)
    dac_trung = any(l.laMonDacTrung for _, l in cac_mon)
    tong = (
        TRONG_SO_QUAN["mon"] * tot_nhat.tong
        + TRONG_SO_QUAN["khoangCach"] * diem_kc
        + TRONG_SO_QUAN["rating"] * diem_rating
        + TRONG_SO_QUAN["nganSach"] * diem_gia
        + TRONG_SO_QUAN["dacTrung"] * (1.0 if dac_trung else 0.0)
    )
    ten_mon = tot_nhat.du_lieu.mon.tenMon
    ly_do = [f"Có {ten_mon}" + (" - món đặc trưng của quán" if link.laMonDacTrung else "")]
    if kc is not None and kc <= 2:
        ly_do.append(f"Cách bạn {kc:.1f} km")
    if rating is not None and rating >= 4.3:
        ly_do.append(f"Đánh giá {rating:.1f}★")
    return DiemQuan(dd, round(tong, 4), kc, [m for m, _ in cac_mon], ly_do)


# ---------------------------------------------------------------- luồng chính


def _nap_du_lieu_mon(db: Session, user: NguoiDung) -> list[DuLieuMon]:
    mons = mon_an_repo.list_active(db)
    ids = [m.idMonAn for m in mons]
    tags = mon_an_repo.so_thich_of(db, ids)
    che_do = mon_an_repo.che_do_an_of(db, ids)
    danh_gia = mon_an_repo.diem_danh_gia_tb(db, ids)
    rating_quan = mon_an_repo.rating_quan_tb(db, ids)
    yeu_thich = mon_an_repo.yeu_thich_ids(db, user.idNguoiDung)
    chay = che_do_an_repo.get_by_ten(db, CHE_DO_CHAY)
    id_chay = chay.idCheDoAn if chay else None

    def _csv(v: str | None) -> set[str]:
        return {x for x in (v or "").split(",") if x}

    return [
        DuLieuMon(
            mon=m,
            buoi=_csv(m.buoiPhuHop),
            thoi_tiet=_csv(m.thoiTietPhuHop),
            gia=float(m.giaThamKhaoTu if m.giaThamKhaoTu is not None else m.giaThamKhaoDen)
            if (m.giaThamKhaoTu is not None or m.giaThamKhaoDen is not None)
            else None,
            tags={st.idSoThich: (st.loai, st.tenSoThich, w) for st, w in tags.get(m.idMonAn, [])},
            che_do=che_do.get(m.idMonAn, set()),
            # ưu tiên điểm review trong app, chưa có thì dùng rating Google của các quán bán món
            danh_gia=danh_gia.get(m.idMonAn, rating_quan.get(m.idMonAn)),
            la_chay=id_chay is not None and id_chay in che_do.get(m.idMonAn, set()),
            la_yeu_thich=m.idMonAn in yeu_thich,
        )
        for m in mons
    ]


def goi_y(db: Session, user: NguoiDung, req: YeuCauGoiY) -> KetQuaGoiYOut:
    req = ngu_canh_service.bo_sung_tu_nhu_cau(db, user, req)
    nc_row = ngu_canh_service.tao_ngu_canh(db, user, req)
    nc = NguCanhCham(
        buoi=nc_row.buoiTrongNgay or Buoi.TRUA.value,
        bua_an=req.buaAn,
        thoi_tiet=nc_row.thoiTiet,
        nhiet_do=float(nc_row.nhietDo) if nc_row.nhietDo is not None else None,
        la_ngay_ram=nc_row.laNgayRam,
        ngan_sach=req.nganSach,
        ghi_chu=req.ghiChu,
        so_thich={st.idSoThich: link.mucDo for link, st in so_thich_repo.list_of_user(db, user.idNguoiDung)},
    )
    che_do_user = {cd.idCheDoAn for _, cd in che_do_an_repo.list_of_user(db, user.idNguoiDung)}

    du_lieu = loc_che_do_an(_nap_du_lieu_mon(db, user), che_do_user)
    du_lieu = loc_nguyen_lieu_tranh(du_lieu, mon_an_repo.mon_chua_nguyen_lieu(db, req.nguyenLieuTranh or []))
    diem_mon = [cham_diem_mon(m, nc) for m in du_lieu]
    top_mon = chon_top_mon(diem_mon, req.soMon)

    # Quán: lấy các quán bán những món điểm cao nhất rồi chấm điểm riêng
    top_xet = sorted(diem_mon, key=lambda d: -d.tong)[:SO_MON_XET_QUAN]
    theo_id = {d.du_lieu.mon.idMonAn: d for d in top_xet}
    nhom: dict[uuid.UUID, tuple[DiaDiem, list[tuple[DiemMon, MonAnDiaDiem]]]] = {}
    for link, dd in dia_diem_repo.quan_of_mons(db, list(theo_id)):
        nhom.setdefault(dd.idDiaDiem, (dd, []))[1].append((theo_id[link.idMonAn], link))
    diem_quan = sorted(
        (
            cham_diem_quan(dd, ds, khoang_cach(dd, req.viDo, req.kinhDo), req.nganSach)
            for dd, ds in nhom.values()
        ),
        key=lambda q: (-q.tong, q.dd.tenDiaDiem),
    )[: req.soDiaDiem]

    mon_out = []
    for hang, d in enumerate(top_mon, 1):
        ly_do = ly_do_mon(d)
        gy = goi_y_repo.create_goi_y(
            db,
            idNguCanh=nc_row.idNguCanh,
            idNguoiDung=user.idNguoiDung,
            idMonAn=d.du_lieu.mon.idMonAn,
            loaiGoiY=LoaiGoiY.MON_AN.value,
            diemSo=Decimal(str(d.tong)),
            thuHang=hang,
            lyDoGiaiThich=ly_do,
        )
        mon_out.append(
            MonGoiYOut(
                idGoiY=gy.idGoiY,
                monAn=MonAnOut.model_validate(d.du_lieu.mon),
                diemSo=d.tong,
                thuHang=hang,
                lyDoGiaiThich=ly_do,
            )
        )
    quan_out = []
    for hang, q in enumerate(diem_quan, 1):
        ly_do = " · ".join(q.ly_do)
        gy = goi_y_repo.create_goi_y(
            db,
            idNguCanh=nc_row.idNguCanh,
            idNguoiDung=user.idNguoiDung,
            idDiaDiem=q.dd.idDiaDiem,
            loaiGoiY=LoaiGoiY.DIA_DIEM.value,
            diemSo=Decimal(str(q.tong)),
            thuHang=hang,
            lyDoGiaiThich=ly_do,
        )
        quan_out.append(
            DiaDiemGoiYOut(
                idGoiY=gy.idGoiY,
                diaDiem=dia_diem_out(q.dd, q.khoang_cach_km),
                diemSo=q.tong,
                thuHang=hang,
                lyDoGiaiThich=ly_do,
                monLienQuan=[MonAnOut.model_validate(m.du_lieu.mon) for m in q.mon[:3]],
            )
        )
    db.commit()
    return KetQuaGoiYOut(nguCanh=NguCanhOut.model_validate(nc_row), monAn=mon_out, diaDiem=quan_out)
