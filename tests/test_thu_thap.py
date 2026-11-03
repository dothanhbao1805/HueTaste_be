"""Pipeline thu thập với Gemini/Wikipedia/Serper giả (monkeypatch), chạy trên SQLite."""
import json

import pytest
from sqlalchemy import func, select

from app.core.constants import LoaiThuThap
from app.models import CheDoAn, DiaDiem, MonAn, MonAnDiaDiem, MonAnSoThich, NguyenLieu, SoThich
from app.repositories import anh_repo
from app.services import llm_service, serper_service, thu_thap_service, wikipedia_service

WIKI = {
    "Bún bò Huế": {"pageid": 1, "extract": "Bún bò Huế là đặc sản của Huế, nước dùng cay nồng."},
    "Bánh bèo": {"pageid": 2, "extract": "Bánh bèo là món bánh nổi tiếng ở Huế."},
}


def _tag(ten, danh_muc="Bún - Bánh canh - Mì", che_do=()):
    return {
        "tenMon": ten,
        "moTa": f"Mô tả {ten}",
        "danhMuc": danh_muc,
        "nguyenLieu": [{"ten": "Bún", "nhom": "tinh bột", "laThanhPhanChinh": True}, {"ten": "Sả", "laThanhPhanChinh": False}],
        "buoiPhuHop": ["sang", "trua", "khong_hop_le"],
        "thoiTietPhuHop": ["lanh", "mua"],
        "giaThamKhaoTu": 35000,
        "giaThamKhaoDen": 60000,
        "vi": [{"ten": "Cay", "trongSo": 0.9}, {"ten": "Vị lạ", "trongSo": 1}],
        "kieu": ["Món nước"],
        "cheDoAn": list(che_do),
    }


@pytest.fixture()
def gia_lap(monkeypatch):
    """Trả về dict để test đổi danh sách món Gemini đề xuất và đọc lại prompt."""
    state = {"danh_sach": [], "prompts": [], "places": {}, "anh": {}, "tim_anh": []}

    def fake_llm(prompt, schema, **kw):
        state["prompts"].append(prompt)
        state.setdefault("thu_tu", []).append(kw.get("thu_tu"))
        if "moTa" not in schema["items"]["properties"]:
            return state["danh_sach"]
        return [_tag(line.split(": ", 1)[1]) for line in prompt.splitlines() if line.startswith("### Món")]

    def fake_tim_trang(tu_khoa, so_ket_qua=5):
        for ten, info in WIKI.items():
            if tu_khoa.lower().startswith(ten.lower()[:6]):
                return [{"title": ten, "pageid": info["pageid"]}]
        return []

    def fake_noi_dung(pageid):
        for ten, info in WIKI.items():
            if info["pageid"] == pageid:
                return {**info, "title": ten, "url": f"https://vi.wikipedia.org/wiki/{pageid}", "anh": "https://img/x.jpg"}
        return None

    def fake_places(tu_khoa, vi_do, kinh_do, so_ket_qua=10):
        # dữ liệu mẫu viết theo dạng JSON của Serper, đi qua chuan_hoa như code thật
        return [serper_service.chuan_hoa(p) for p in state["places"].get(tu_khoa, [])]

    def fake_anh(tu_khoa, so_anh=10):
        state["tim_anh"].append(tu_khoa)
        return [serper_service.chuan_hoa_anh(a) for a in state["anh"].get(tu_khoa, [])]

    monkeypatch.setattr(serper_service, "tim_anh", fake_anh)
    monkeypatch.setattr(llm_service, "generate_json", fake_llm)
    monkeypatch.setattr(wikipedia_service, "tim_trang", fake_tim_trang)
    monkeypatch.setattr(wikipedia_service, "lay_noi_dung", fake_noi_dung)
    monkeypatch.setattr(serper_service, "tim_quan", fake_places)
    return state


def _dem(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_thu_thap_mon_an_xac_minh_va_khong_trung(db_session, gia_lap):
    gia_lap["danh_sach"] = [
        {"tenMon": "Bún bò Huế", "tenGoiKhac": ["Bún bò"], "danhMuc": "Bún - Bánh canh - Mì"},
        {"tenMon": "Bánh bèo", "danhMuc": "Bánh Huế"},
        {"tenMon": "bún bò  HUẾ", "danhMuc": "Bún - Bánh canh - Mì"},  # Gemini lặp trong cùng danh sách
        {"tenMon": "Món bịa đặt", "danhMuc": "Ăn vặt"},
    ]
    tk = thu_thap_service.thu_thap_mon_an(db_session, 10)
    assert tk == {"deXuat": 3, "moi": 3, "capNhat": 0, "chuaXacMinh": 1, "loi": 0, "anhMon": 0}
    # bước liệt kê món và bước trích tag dùng thứ tự nhà cung cấp riêng
    from app.core.config import settings

    assert gia_lap["thu_tu"][0] == settings.LLM_THU_TU_DANH_SACH
    assert set(gia_lap["thu_tu"][1:]) == {settings.LLM_THU_TU_TAG}

    mons = {m.tenMon: m for m in db_session.scalars(select(MonAn)).all()}
    assert mons["Bún bò Huế"].trangThai == "active" and mons["Bún bò Huế"].maWikipedia == 1
    assert mons["Bún bò Huế"].tenChuanHoa == "bun bo hue"
    assert mons["Bún bò Huế"].nguonThamKhao.endswith("/1")
    assert mons["Bún bò Huế"].buoiPhuHop == "sang,trua"  # giá trị ngoài enum bị bỏ
    assert mons["Món bịa đặt"].trangThai == "unverified" and mons["Món bịa đặt"].maWikipedia is None
    # tag: chỉ nhận vị trong danh sách cho phép
    assert {s.tenSoThich for s in db_session.scalars(select(SoThich)).all()} == {"Cay", "Món nước"}
    assert _dem(db_session, NguyenLieu) == 2

    # Lần 2: Gemini đề xuất lại món cũ + tên gọi khác trỏ cùng bài Wikipedia -> không sinh bản ghi mới
    gia_lap["danh_sach"] = [
        {"tenMon": "Bún bò Huế", "danhMuc": "Bún - Bánh canh - Mì"},
        {"tenMon": "Bún bò", "danhMuc": "Bún - Bánh canh - Mì"},
    ]
    tk2 = thu_thap_service.thu_thap_mon_an(db_session, 10)
    assert tk2["moi"] == 0 and tk2["capNhat"] == 1  # "Bún bò Huế" bị bỏ ngay, "Bún bò" gộp theo pageid
    assert _dem(db_session, MonAn) == 3
    assert _dem(db_session, NguyenLieu) == 2 and _dem(db_session, MonAnSoThich) == 6
    # prompt lần 2 đã gửi kèm danh sách món có sẵn
    assert "Bún bò Huế" in gia_lap["prompts"][-2] and "KHÔNG lặp lại" in gia_lap["prompts"][-2]


def test_thu_thap_mon_chay_tao_che_do_an(db_session, gia_lap, monkeypatch):
    gia_lap["danh_sach"] = [{"tenMon": "Bánh bèo", "danhMuc": "Bánh Huế"}]
    monkeypatch.setattr(
        llm_service,
        "generate_json",
        lambda prompt, schema, **_: gia_lap["danh_sach"]
        if "moTa" not in schema["items"]["properties"]
        else [_tag("Bánh bèo", "Bánh Huế", che_do=["Ăn chay", "Không tồn tại"])],
    )
    thu_thap_service.thu_thap_mon_an(db_session, 5)
    assert [c.tenCheDo for c in db_session.scalars(select(CheDoAn)).all()] == ["Ăn chay"]


def _place(pid, ten, lat=16.47, lng=107.59, rating=4.6):
    return {
        "placeId": pid,
        "title": ten,
        "address": "Huế",
        "latitude": lat,
        "longitude": lng,
        "rating": rating,
        "ratingCount": 120,
        "priceLevel": "₫",
        "openingHours": {"Thứ Hai": "6:00–22:00"},
        "thumbnailUrl": f"https://lh5.googleusercontent.com/{pid}",
    }


def test_thu_thap_dia_diem_khong_trung(db_session, gia_lap):
    gia_lap["danh_sach"] = [
        {"tenMon": "Bún bò Huế", "danhMuc": "Bún - Bánh canh - Mì"},
        {"tenMon": "Bánh bèo", "danhMuc": "Bánh Huế"},
    ]
    thu_thap_service.thu_thap_mon_an(db_session, 5)
    gia_lap["places"] = {
        "Bún bò Huế": [_place("p1", "Bún bò Huế O Phượng"), _place("p9", "Quán Đà Nẵng", 16.05, 108.2)],
        "Bánh bèo Huế": [_place("p1", "Bún bò Huế O Phượng"), _place("p2", "Bánh bèo Bà Đỏ")],
    }
    for _ in range(2):  # chạy 2 lần vẫn không trùng
        tk = thu_thap_service.thu_thap_dia_diem(db_session, 8)
    assert tk["quanMoi"] == 0 and tk["quanCapNhat"] == 3
    assert _dem(db_session, DiaDiem) == 2  # p9 ngoài bán kính Huế bị loại
    assert _dem(db_session, MonAnDiaDiem) == 3
    p1 = db_session.scalar(select(DiaDiem).where(DiaDiem.maGooglePlace == "p1"))
    # rating Google lưu riêng; chưa có đánh giá app nên điểm trung bình = rating Google
    assert float(p1.diemGoogle) == 4.6 and p1.soDanhGiaGoogle == 120
    assert p1.mucGia == 1 and float(p1.diemTrungBinh) == 4.6 and p1.hinhAnh == "https://lh5.googleusercontent.com/p1"
    assert json.loads(p1.gioMoCua) == ["Thứ Hai: 6:00–22:00"]
    dac_trung = db_session.scalars(select(MonAnDiaDiem.laMonDacTrung).where(MonAnDiaDiem.idDiaDiem == p1.idDiaDiem)).all()
    assert sorted(dac_trung) == [False, True]  # quán tên "Bún bò Huế..." là đặc trưng cho bún bò


def test_tim_quan_xac_minh_mon_unverified_nho_quan_mang_ten_mon(db_session, gia_lap):
    """Món Huế không có bài Wikipedia (unverified) được bật lên khi Google Maps có quán mang tên món."""
    gia_lap["danh_sach"] = [
        {"tenMon": "Bánh canh Nam Phổ", "danhMuc": "Bún - Bánh canh - Mì"},
        {"tenMon": "Bánh ép Huế", "danhMuc": "Bánh Huế"},
        {"tenMon": "Món bịa đặt", "danhMuc": "Ăn vặt"},
    ]
    thu_thap_service.thu_thap_mon_an(db_session, 5)
    assert {m.trangThai for m in db_session.scalars(select(MonAn))} == {"unverified"}
    gia_lap["places"] = {
        "Bánh canh Nam Phổ Huế": [_place("p1", "Bánh canh Nam Phổ Bà Đợi")],
        "Bánh ép Huế": [_place("p2", "Bánh ép Bà Đỏ")],  # bỏ đuôi "Huế" khi so tên
        "Món bịa đặt Huế": [_place("p3", "Quán cơm gần đó")],  # Maps luôn trả quán, nhưng không mang tên món
    }
    tk = thu_thap_service.thu_thap_dia_diem(db_session, 8)
    assert tk["monXacMinh"] == 2 and tk["monDaXet"] == 3
    trang_thai = {m.tenMon: m.trangThai for m in db_session.scalars(select(MonAn))}
    assert trang_thai == {"Bánh canh Nam Phổ": "active", "Bánh ép Huế": "active", "Món bịa đặt": "unverified"}


def test_ten_mon_trong_ten_quan():
    khop = thu_thap_service.ten_mon_trong_ten_quan
    assert khop("Bánh ép Huế", "Bánh ép Bà Đỏ") and khop("Bún bò Huế", "BÚN BÒ HUẾ O Phượng")
    assert not khop("Chè Huế", "Chè bắp Cồn Hến")  # "Chè Huế" không bị rút còn "chè"
    assert not khop("Bánh bèo", "Bánh bèoxx")  # so nguyên từ


def test_chay_dung_khi_thieu_key(db_session, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    kq = thu_thap_service.chay(LoaiThuThap.MON_AN, 5, session_factory=lambda: _KhongDong(db_session))
    assert "GROQ_API_KEY hoặc GEMINI_API_KEY" in kq["loi"]


class _KhongDong:
    """Bọc session test để `with session_factory() as db` không đóng session dùng chung."""

    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, *_):
        return False


def test_unique_db_chan_trung_khi_tra_cuu_bo_sot(db_session, gia_lap, monkeypatch):
    """Mô phỏng 2 lần chạy đua nhau: lần tra cứu đầu không thấy món nhưng DB đã có -> unique chặn,
    savepoint rollback rồi chuyển sang cập nhật, không sinh bản ghi trùng."""
    from app.repositories import mon_an_repo

    gia_lap["danh_sach"] = [{"tenMon": "Món bịa đặt", "danhMuc": "Ăn vặt"}]
    thu_thap_service.thu_thap_mon_an(db_session, 5)

    goc = mon_an_repo.get_by_ten_chuan_hoa
    lan_goi = {"n": 0}

    def bo_sot_lan_dau(db, keys):
        lan_goi["n"] += 1
        return None if lan_goi["n"] == 1 else goc(db, keys)

    monkeypatch.setattr(mon_an_repo, "get_by_ten_chuan_hoa", bo_sot_lan_dau)
    monkeypatch.setattr(mon_an_repo, "list_ten_chuan_hoa", lambda db: set())
    tk = thu_thap_service.thu_thap_mon_an(db_session, 5)
    assert tk["moi"] == 0 and tk["capNhat"] == 1 and tk["loi"] == 0
    assert _dem(db_session, MonAn) == 1



def _anh(url, tieu_de, rong=800):
    return {"imageUrl": url, "thumbnailUrl": url + "?t", "title": tieu_de, "source": "site.vn", "imageWidth": rong}


def test_thu_thap_nhieu_anh_cho_mon_va_quan(db_session, gia_lap):
    gia_lap["danh_sach"] = [{"tenMon": "Bún bò Huế", "danhMuc": "Bún - Bánh canh - Mì"}]
    gia_lap["anh"] = {
        "Bún bò Huế món ăn": [
            _anh("https://a/1.jpg", "Bún bò Huế ngon"),
            _anh("https://a/1.jpg", "Bún bò Huế ngon"),  # trùng URL
            _anh("https://a/2.jpg", "Cơm hến"),  # lạc đề
            _anh("https://a/3.jpg", "Bún bò Huế chuẩn vị", rong=100),  # quá nhỏ
            _anh("ftp://a/4.jpg", "Bún bò Huế"),  # không phải http(s)
            _anh("https://a/5.jpg", "BÚN BÒ HUẾ O Phượng"),
        ],
        "Bún bò Huế O Phượng Huế": [_anh("https://q/1.jpg", "Bún bò Huế O Phượng - menu")],
    }
    tk = thu_thap_service.thu_thap_mon_an(db_session, 5)
    assert tk["anhMon"] == 2
    mon = db_session.scalar(select(MonAn))
    assert [a.url for a in anh_repo.list_mon(db_session, mon.idMonAn)] == ["https://a/1.jpg", "https://a/5.jpg"]
    assert mon.hinhAnh == "https://img/x.jpg"  # ảnh bìa Wikipedia giữ nguyên

    # chạy lại: món đã đủ ảnh nên không tốn thêm lượt Serper Images
    so_lan = len(gia_lap["tim_anh"])
    assert thu_thap_service.thu_thap_mon_an(db_session, 5)["anhMon"] == 0
    assert len(gia_lap["tim_anh"]) == so_lan

    gia_lap["places"] = {"Bún bò Huế": [_place("p1", "Bún bò Huế O Phượng")]}
    tk = thu_thap_service.thu_thap_dia_diem(db_session, 8)
    assert tk["anhQuan"] == 2  # thumbnail Maps + 1 ảnh Serper
    dd = db_session.scalar(select(DiaDiem))
    assert [a.url for a in anh_repo.list_dia_diem(db_session, dd.idDiaDiem)] == [
        "https://lh5.googleusercontent.com/p1",
        "https://q/1.jpg",
    ]
    assert dd.hinhAnh == "https://lh5.googleusercontent.com/p1"


def test_loi_tim_anh_khong_lam_hong_viec_luu_mon(db_session, gia_lap, monkeypatch):
    from app.core.exceptions import ExternalServiceError

    def loi(*_a, **_k):
        raise ExternalServiceError("Serper lỗi", "SERPER_NOT_CONFIGURED")

    monkeypatch.setattr(serper_service, "tim_anh", loi)
    gia_lap["danh_sach"] = [{"tenMon": "Bún bò Huế", "danhMuc": "Bún - Bánh canh - Mì"}]
    tk = thu_thap_service.thu_thap_mon_an(db_session, 5)
    assert tk["moi"] == 1 and tk["loi"] == 0 and tk["anhMon"] == 0
    assert _dem(db_session, MonAn) == 1


def test_tat_thu_thap_anh(db_session, gia_lap, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "THU_THAP_ANH_BAT", False)
    gia_lap["danh_sach"] = [{"tenMon": "Bún bò Huế", "danhMuc": "Bún - Bánh canh - Mì"}]
    thu_thap_service.thu_thap_mon_an(db_session, 5)
    assert gia_lap["tim_anh"] == []


def test_chuan_hoa_anh_serper():
    a = serper_service.chuan_hoa_anh(
        {"imageUrl": "https://x/a.jpg", "thumbnailUrl": "https://t/a", "title": "T", "source": "x.vn", "imageWidth": 640}
    )
    assert a == {
        "url": "https://x/a.jpg", "thumbnail": "https://t/a", "nguon": "x.vn", "tieuDe": "T", "rong": 640, "cao": None
    }


def test_chuan_hoa_ket_qua_serper():
    p = serper_service.chuan_hoa(
        {
            "title": "Bún bò O Phượng",
            "address": "Huế",
            "latitude": 16.47,
            "longitude": 107.59,
            "rating": 4.5,
            "priceLevel": "₫₫",
            "phoneNumber": "0234 123",
            "openingHours": {"Thứ Hai": "6:00–22:00"},
            "thumbnailUrl": "https://lh5.googleusercontent.com/x",
            "cid": 123456,
        }
    )
    assert p["id"] == "123456" and p["ten"] == "Bún bò O Phượng" and p["mucGia"] == 2
    assert p["gioMoCua"] == ["Thứ Hai: 6:00–22:00"] and p["anh"].startswith("https://")
    # placeId được ưu tiên hơn cid; mức giá dạng khoảng tiền không quy đổi được -> None
    p2 = serper_service.chuan_hoa({"placeId": "ChIJabc", "cid": "1", "priceLevel": "1–100.000 ₫"})
    assert p2["id"] == "ChIJabc" and p2["mucGia"] is None and p2["gioMoCua"] is None
