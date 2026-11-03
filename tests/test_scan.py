"""Scan ảnh món ăn: model vision và pipeline tìm hiểu món đều giả lập (monkeypatch), chạy trên SQLite."""
import httpx
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models import LichSuScan, MonAn, MonAnDiaDiem
from app.services import gemini_service, scan_service, thu_thap_service
from tests.conftest import auth_header
from tests.du_lieu_mau import tao_du_lieu
from tests.test_admin import _admin_token
from tests.test_thu_thap import WIKI, _KhongDong, _place, gia_lap  # noqa: F401  (fixture)

URL = "/api/v1/scan"
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def _kq(ten_ds="KHAC", ten_that="", la_mon_an=True, la_hue=True, giong=()):
    return {
        "laMonAn": la_mon_an,
        "tenMonTrongDanhSach": ten_ds,
        "tenMonThucTe": ten_that or ten_ds,
        "laMonDacTrungHue": la_hue,
        "danhMuc": "Cơm - Cháo",
        "doTinCay": 0.97,
        "moTaNgan": f"Giới thiệu {ten_that or ten_ds}",
        "monGanGiong": list(giong),
    }


@pytest.fixture()
def moi_truong(monkeypatch, tmp_path, db_session):
    """Ảnh lưu vào tmp, model vision trả `state["kq"]`, background task dùng session test."""
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(thu_thap_service, "SessionLocal", lambda: _KhongDong(db_session))
    scan_service._dang_lam_giau.clear()
    scan_service._lan_thu_cuoi.clear()
    state = {"kq": _kq(), "prompts": []}

    def fake_nhan_dien(anh, mime, prompt, schema):
        state["prompts"].append(prompt)
        assert mime == "image/jpeg" and anh == JPG
        return state["kq"]

    monkeypatch.setattr(gemini_service, "nhan_dien_anh", fake_nhan_dien)
    return state


def _scan(client, token):
    return client.post(URL, files={"file": ("a.jpg", JPG, "image/jpeg")}, headers=auth_header(token))


def test_scan_mon_da_co_tra_chi_tiet(client, db_session, user_token, moi_truong):
    tao_du_lieu(db_session)
    moi_truong["kq"] = _kq("Bún bò Huế")
    r = _scan(client, user_token)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["trangThai"] == "CO_TRONG_HE_THONG" and body["monAn"]["tenMon"] == "Bún bò Huế"
    assert body["monAn"]["diaDiem"][0]["diaDiem"]["tenDiaDiem"] == "Bún bò O Phượng"
    assert body["duongDanAnh"].startswith("http://testserver/uploads/scan/")
    # danh sách gửi model gồm cả món unverified để không tạo trùng
    assert "Món chưa xác minh" in moi_truong["prompts"][0] and "đặc trưng" in moi_truong["prompts"][0]
    scan = db_session.scalar(select(LichSuScan))
    assert str(scan.idMonAn) == body["idMonAn"]
    assert float(scan.doTinCay) == 0.97


def test_scan_khop_gan_dung_khi_model_viet_lech_ten(client, db_session, user_token, moi_truong):
    tao_du_lieu(db_session)
    moi_truong["kq"] = _kq("KHAC", "Bánh bèo.")
    assert _scan(client, user_token).json()["monAn"]["tenMon"] == "Bánh bèo"


def test_scan_mon_hue_moi_tim_hieu_nen_qua_wikipedia(client, db_session, user_token, moi_truong, gia_lap, monkeypatch):
    tao_du_lieu(db_session)
    monkeypatch.setitem(WIKI, "Cơm hến", {"pageid": 7, "extract": "Cơm hến là món ăn dân dã của Huế."})
    gia_lap["places"] = {"Cơm hến Huế": [_place("p7", "Cơm hến Hoa Đông")]}
    # chặn background task để kiểm tra trạng thái lúc đang tìm hiểu
    monkeypatch.setattr(scan_service, "_lam_giau", lambda id_mon: None)
    moi_truong["kq"] = _kq("KHAC", "Cơm hến", giong=["Bún bò Huế", "Món chưa xác minh"])
    r = _scan(client, user_token)
    body = r.json()
    assert r.status_code == 200 and body["trangThai"] == "DANG_CAP_NHAT" and body["tenMonNhanDien"] == "Cơm hến"
    assert [m["tenMon"] for m in body["monTuongTu"]] == ["Bún bò Huế"]  # chỉ món active
    mon = db_session.scalar(select(MonAn).where(MonAn.tenMon == "Cơm hến"))
    assert mon.trangThai == "unverified" and mon.moTa == "Giới thiệu Cơm hến"

    # chạy phần tìm hiểu nền như background task thật
    scan_service._dang_lam_giau.pop(mon.idMonAn, None)
    thu_thap_service.lam_giau_mon(mon.idMonAn)
    db_session.refresh(mon)
    assert mon.trangThai == "active" and mon.maWikipedia == 7
    r = client.get(f"{URL}/{body['idLichSuScan']}", headers=auth_header(user_token))
    assert r.json()["trangThai"] == "CO_TRONG_HE_THONG"
    assert r.json()["monAn"]["diaDiem"][0]["diaDiem"]["tenDiaDiem"] == "Cơm hến Hoa Đông"
    assert r.json()["monAn"]["nguyenLieu"]  # tag do LLM trích


def test_scan_mon_hue_moi_background_chay_ngay(client, db_session, user_token, moi_truong, gia_lap):
    """TestClient chạy BackgroundTasks ngay sau response: Wikipedia không có nhưng Serper có quán mang tên món."""
    tao_du_lieu(db_session)
    gia_lap["places"] = {"Bánh khoái Huế": [_place("p8", "Bánh khoái Lạc Thiện")]}
    moi_truong["kq"] = _kq("KHAC", "Bánh khoái")
    body = _scan(client, user_token).json()
    assert body["trangThai"] == "DANG_CAP_NHAT"
    r = client.get(f"{URL}/{body['idLichSuScan']}", headers=auth_header(user_token))
    assert r.json()["trangThai"] == "CO_TRONG_HE_THONG" and r.json()["monAn"]["tenMon"] == "Bánh khoái"
    mon = db_session.scalar(select(MonAn).where(MonAn.tenMon == "Bánh khoái"))
    assert mon.maWikipedia is None and db_session.scalar(select(MonAnDiaDiem).where(MonAnDiaDiem.idMonAn == mon.idMonAn))


def test_scan_mon_hue_moi_khong_xac_minh_duoc(client, db_session, user_token, moi_truong, gia_lap):
    tao_du_lieu(db_session)
    moi_truong["kq"] = _kq("KHAC", "Bánh tưởng tượng")
    body = _scan(client, user_token).json()
    r = client.get(f"{URL}/{body['idLichSuScan']}", headers=auth_header(user_token))
    assert r.json()["trangThai"] == "CHUA_XAC_MINH" and r.json()["moTaNgan"]
    ten = [m["tenMon"] for m in client.get("/api/v1/mon-an").json()["items"]]
    assert "Bánh tưởng tượng" not in ten
    # scan lại trong ngày: không tìm hiểu lại, không tạo trùng
    assert _scan(client, user_token).json()["trangThai"] == "CHUA_XAC_MINH"
    assert len(db_session.scalars(select(MonAn).where(MonAn.tenMon == "Bánh tưởng tượng")).all()) == 1


def test_scan_mon_khong_dac_trung_hue_khong_luu(client, db_session, user_token, moi_truong, admin_user):
    tao_du_lieu(db_session)
    so_mon = len(db_session.scalars(select(MonAn)).all())
    moi_truong["kq"] = _kq("KHAC", "Pizza", la_hue=False, giong=["Bánh bèo"])
    for _ in range(2):
        body = _scan(client, user_token).json()
    assert body["trangThai"] == "KHONG_LUU" and body["idMonAn"] is None and body["monAn"] is None
    assert [m["tenMon"] for m in body["monTuongTu"]] == ["Bánh bèo"]
    assert len(db_session.scalars(select(MonAn)).all()) == so_mon

    h = auth_header(_admin_token(client))
    r = client.get("/api/v1/admin/scan/mon-khong-luu", headers=h)
    assert r.status_code == 200
    assert [(m["tenMon"], m["soLanScan"], m["soNguoiScan"]) for m in r.json()] == [("Pizza", 2, 1)]
    assert client.get("/api/v1/admin/scan/mon-khong-luu", headers=auth_header(user_token)).status_code == 403


def test_scan_khong_phai_mon_an(client, db_session, user_token, moi_truong):
    moi_truong["kq"] = _kq(la_mon_an=False, ten_that="Con mèo")
    r = _scan(client, user_token)
    assert r.status_code == 422 and r.json()["code"] == "KHONG_NHAN_DIEN_DUOC"
    assert db_session.scalar(select(LichSuScan)) is not None  # vẫn ghi lịch sử


def test_scan_loi_dau_vao_va_gioi_han(client, user_token, moi_truong, monkeypatch):
    r = client.post(URL, files={"file": ("a.jpg", b"hello", "image/jpeg")}, headers=auth_header(user_token))
    assert r.status_code == 400 and r.json()["code"] == "INVALID_IMAGE"
    assert client.post(URL, files={"file": ("a.jpg", JPG, "image/jpeg")}).status_code == 401
    monkeypatch.setattr(settings, "SCAN_TOI_DA_MOI_NGAY", 1)
    moi_truong["kq"] = _kq("KHAC", "Pizza", la_hue=False)
    assert _scan(client, user_token).status_code == 200
    r = _scan(client, user_token)
    assert r.status_code == 429 and r.json()["code"] == "SCAN_QUA_GIOI_HAN"


def test_lich_su_va_ket_qua_chi_cua_minh(client, db_session, user_token, moi_truong):
    tao_du_lieu(db_session)
    moi_truong["kq"] = _kq("Bánh bèo")
    id_scan = _scan(client, user_token).json()["idLichSuScan"]
    r = client.get("/api/v1/users/me/lich-su-scan", headers=auth_header(user_token))
    assert r.json()["total"] == 1 and r.json()["items"][0]["tenMonNhanDien"] == "Bánh bèo"

    r2 = client.post("/api/v1/auth/register", json={"email": "b@test.com", "matKhau": "password123", "hoTen": "B"})
    khac = auth_header(r2.json()["accessToken"])
    assert client.get(f"{URL}/{id_scan}", headers=khac).status_code == 404
    assert client.get("/api/v1/users/me/lich-su-scan", headers=khac).json()["total"] == 0


def test_scan_model_loi_het(client, user_token, moi_truong, monkeypatch):
    from app.core.exceptions import ExternalServiceError

    def loi(*_):
        raise ExternalServiceError("hết model", "SCAN_KHONG_KHA_DUNG")

    monkeypatch.setattr(gemini_service, "nhan_dien_anh", loi)
    r = _scan(client, user_token)
    assert r.status_code == 502 and r.json()["code"] == "SCAN_KHONG_KHA_DUNG"


# ---------------------------------------------------------------- gemini_service.nhan_dien_anh


class _Resp:
    def __init__(self, status, data):
        self.status_code, self._data, self.text = status, data, str(data)

    def json(self):
        return self._data


def _tra_loi(text):
    return _Resp(200, {"candidates": [{"content": {"parts": [{"text": "suy nghĩ", "thought": True}, {"text": text}]}}]})


def test_nhan_dien_anh_chuyen_model_khi_loi(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(settings, "GEMINI_MODEL_SCAN", "m1,m2,gemma-x")
    goi = []

    def fake_post(url, headers, json, timeout):
        goi.append((url, json["generationConfig"]))
        if "m1" in url:
            raise httpx.ReadTimeout("chậm")
        if "m2" in url:
            return _Resp(503, {"error": "quá tải"})
        return _tra_loi('Kết quả: {"laMonAn": true, "tenMonThucTe": "Cơm hến"} xong')

    monkeypatch.setattr(httpx, "post", fake_post)
    kq = gemini_service.nhan_dien_anh(JPG, "image/jpeg", "p", {"type": "OBJECT"})
    assert kq == {"laMonAn": True, "tenMonThucTe": "Cơm hến"}
    assert len(goi) == 3
    assert "responseSchema" in goi[0][1] and "responseSchema" not in goi[2][1]  # Gemma không nhận schema


def test_nhan_dien_anh_het_model(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(settings, "GEMINI_MODEL_SCAN", "m1")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _tra_loi("không có json"))
    with pytest.raises(Exception) as e:
        gemini_service.nhan_dien_anh(JPG, "image/jpeg", "p", {})
    assert e.value.code == "SCAN_KHONG_KHA_DUNG"
