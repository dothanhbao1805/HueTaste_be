from decimal import Decimal

from sqlalchemy import func, select

from app.models import DanhGia
from tests.conftest import auth_header
from tests.du_lieu_mau import tao_du_lieu

URL = "/api/v1/danh-gia"


def _dang_ky(client, email, ho_ten="Khách"):
    r = client.post("/api/v1/auth/register", json={"email": email, "matKhau": "password123", "hoTen": ho_ten})
    return auth_header(r.json()["accessToken"])


def _quan_co_rating_google(db_session, d, diem="4.0", so=3):
    quan = d["gan"]
    quan.diemGoogle, quan.soDanhGiaGoogle = Decimal(diem), so
    db_session.commit()
    return quan


def test_viet_va_viet_lai_danh_gia_mon(client, db_session, user_token):
    d = tao_du_lieu(db_session)
    h = auth_header(user_token)
    id_mon = str(d["bun_bo"].idMonAn)
    r = client.post(URL, json={"idMonAn": id_mon, "diemSo": 4, "noiDung": "Ngon"}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["nguoiDung"]["hoTen"] == "Nguyen Van A" and r.json()["idMonAn"] == id_mon
    # viết lại -> cập nhật, vẫn 1 bản ghi
    client.post(URL, json={"idMonAn": id_mon, "diemSo": 2}, headers=h)
    assert db_session.scalar(select(func.count()).select_from(DanhGia)) == 1

    client.post(URL, json={"idMonAn": id_mon, "diemSo": 5}, headers=_dang_ky(client, "b@test.com", "B"))
    trang = client.get(f"/api/v1/mon-an/{id_mon}/danh-gia").json()  # công khai
    assert trang["total"] == 2 and trang["diemTrungBinh"] == 3.5
    assert {x["diemSo"] for x in trang["items"]} == {2, 5}
    assert len(client.get(f"/api/v1/mon-an/{id_mon}/danh-gia", params={"size": 1}).json()["items"]) == 1


def test_diem_quan_gop_google_va_app(client, db_session, user_token):
    d = tao_du_lieu(db_session)
    quan = _quan_co_rating_google(db_session, d)  # Google 4.0 x 3 lượt
    h = auth_header(user_token)
    r = client.post(URL, json={"idDiaDiem": str(quan.idDiaDiem), "diemSo": 5}, headers=h)
    assert r.status_code == 201
    db_session.refresh(quan)
    assert quan.diemTrungBinh == Decimal("4.25")  # (4.0*3 + 5) / 4

    trang = client.get(f"/api/v1/dia-diem/{quan.idDiaDiem}/danh-gia").json()
    assert trang["total"] == 1 and trang["diemTrungBinh"] == 4.25

    # xóa đánh giá -> về lại rating Google
    assert client.delete(f"{URL}/{r.json()['idDanhGia']}", headers=h).status_code == 200
    db_session.refresh(quan)
    assert quan.diemTrungBinh == Decimal("4.00")


def test_danh_gia_validate_va_quyen(client, db_session, user_token):
    d = tao_du_lieu(db_session)
    h = auth_header(user_token)
    id_mon = str(d["bun_bo"].idMonAn)
    assert client.post(URL, json={"idMonAn": id_mon, "diemSo": 6}, headers=h).status_code == 422
    assert client.post(URL, json={"diemSo": 3}, headers=h).status_code == 422
    assert client.post(URL, json={"idMonAn": id_mon, "diemSo": 3}).status_code == 401
    r = client.post(URL, json={"idMonAn": str(d["bi_an"].idMonAn), "diemSo": 3}, headers=h)
    assert r.status_code == 404

    id_dg = client.post(URL, json={"idMonAn": id_mon, "diemSo": 3}, headers=h).json()["idDanhGia"]
    r = client.delete(f"{URL}/{id_dg}", headers=_dang_ky(client, "khac@test.com"))
    assert r.status_code == 404 and r.json()["code"] == "DANH_GIA_NOT_FOUND"
    assert client.get(f"/api/v1/mon-an/{d['bi_an'].idMonAn}/danh-gia").status_code == 404
