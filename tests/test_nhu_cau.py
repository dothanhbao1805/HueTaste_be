import uuid
from datetime import datetime

from sqlalchemy import func, select

from app.models import NguCanh, NhuCauTheoNgay
from app.services.ngu_canh_service import TZ_VN
from tests.conftest import auth_header
from tests.du_lieu_mau import tao_du_lieu
from tests.test_goi_y import co_dinh_ngu_canh  # noqa: F401  fixture

URL = "/api/v1/users/me/nhu-cau"


def _dang_ky(client, email):
    r = client.post("/api/v1/auth/register", json={"email": email, "matKhau": "password123", "hoTen": "B"})
    return auth_header(r.json()["accessToken"])


def test_upsert_list_va_xoa(client, db_session, user_token):
    h = auth_header(user_token)
    r = client.put(URL, json={"buaAn": "trua", "nganSach": 50000, "ghiChu": "ít cay"}, headers=h)
    assert r.status_code == 200 and r.json()["nganSach"] == 50000 and r.json()["ngay"] == datetime.now(TZ_VN).date().isoformat()
    # cùng ngày + bữa -> cập nhật, không tạo bản mới
    r = client.put(URL, json={"buaAn": "trua", "nganSach": 70000}, headers=h)
    assert r.json()["nganSach"] == 70000 and r.json()["ghiChu"] is None
    client.put(URL, json={"buaAn": "toi", "ngay": "2030-01-01"}, headers=h)
    assert db_session.scalar(select(func.count()).select_from(NhuCauTheoNgay)) == 2

    assert [n["buaAn"] for n in client.get(URL, headers=h).json()] == ["trua"]
    ds = client.get(URL, params={"ngay": "2030-01-01"}, headers=h).json()
    assert [n["buaAn"] for n in ds] == ["toi"]

    # người khác không xóa được
    h_khac = _dang_ky(client, "khac@test.com")
    r = client.delete(f"{URL}/{ds[0]['idNhuCauTheoNgay']}", headers=h_khac)
    assert r.status_code == 404 and r.json()["code"] == "NHU_CAU_NOT_FOUND"
    assert client.delete(f"{URL}/{ds[0]['idNhuCauTheoNgay']}", headers=h).status_code == 200


def test_validate_va_auth(client, user_token):
    assert client.get(URL).status_code == 401
    r = client.put(URL, json={"buaAn": "an_trua"}, headers=auth_header(user_token))
    assert r.status_code == 422
    r = client.put(URL, json={"buaAn": "sang", "nganSach": -1}, headers=auth_header(user_token))
    assert r.status_code == 422


def test_goi_y_dung_lai_nhu_cau_da_luu(client, db_session, user_token, co_dinh_ngu_canh):  # noqa: F811
    tao_du_lieu(db_session)
    h = auth_header(user_token)
    id_nc = client.put(URL, json={"buaAn": "sang", "nganSach": 30000, "ghiChu": "món ngọt"}, headers=h).json()[
        "idNhuCauTheoNgay"
    ]
    # gửi chỉ buaAn: dùng ngân sách/ghi chú đã lưu và không ghi đè chúng thành NULL
    r = client.post("/api/v1/goi-y", json={"buaAn": "sang"}, headers=h)
    assert r.status_code == 200, r.text
    nc = db_session.scalar(select(NguCanh))
    assert str(nc.idNhuCauTheoNgay) == id_nc
    luu = db_session.get(NhuCauTheoNgay, nc.idNhuCauTheoNgay)
    assert int(luu.nganSach) == 30000 and luu.ghiChu == "món ngọt"


def test_gio_an_va_nguyen_lieu_tranh(client, db_session, user_token):
    du_lieu = tao_du_lieu(db_session)
    h = auth_header(user_token)
    id_tom = str(du_lieu["tom"].idNguyenLieu)
    body = {"buaAn": "sang", "gioAn": "06:30", "nguyenLieuTranh": [id_tom, id_tom]}
    r = client.put(URL, json=body, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["gioAn"] == "06:30:00"
    assert [n["tenNguyenLieu"] for n in r.json()["nguyenLieuTranh"]] == ["Tôm"]  # bỏ trùng
    assert client.get(URL, headers=h).json()[0]["nguyenLieuTranh"][0]["idNguyenLieu"] == id_tom

    r = client.put(URL, json={"buaAn": "sang", "nguyenLieuTranh": [str(uuid.uuid4())]}, headers=h)
    assert r.status_code == 400 and r.json()["code"] == "NGUYEN_LIEU_NOT_FOUND"


def test_goi_y_khong_ghi_de_gio_an_va_nguyen_lieu(client, db_session, user_token, co_dinh_ngu_canh):  # noqa: F811
    du_lieu = tao_du_lieu(db_session)
    h = auth_header(user_token)
    body = {"buaAn": "trua", "gioAn": "11:30", "nguyenLieuTranh": [str(du_lieu["tom"].idNguyenLieu)]}
    client.put(URL, json=body, headers=h)
    assert client.post("/api/v1/goi-y", json={"buaAn": "trua", "nganSach": 60000}, headers=h).status_code == 200
    nc = client.get(URL, headers=h).json()[0]
    assert nc["gioAn"] == "11:30:00" and nc["nganSach"] == 60000
    assert [n["tenNguyenLieu"] for n in nc["nguyenLieuTranh"]] == ["Tôm"]
