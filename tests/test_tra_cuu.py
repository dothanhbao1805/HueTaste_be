import uuid

from app.repositories import anh_repo
from app.services import thu_thap_service
from tests.conftest import auth_header
from tests.du_lieu_mau import tao_du_lieu

API = "/api/v1"


def test_danh_muc_va_tim_mon(client, db_session):
    du_lieu = tao_du_lieu(db_session)
    assert {d["tenDanhMuc"] for d in client.get(f"{API}/danh-muc").json()} >= {"Bánh Huế"}

    r = client.get(f"{API}/mon-an", params={"q": "bun bo"}).json()  # gõ không dấu
    assert r["total"] == 1 and r["items"][0]["tenMon"] == "Bún bò Huế"
    assert r["items"][0]["buoiPhuHop"] == ["sang", "trua"] and r["items"][0]["giaThamKhaoTu"] == 40000

    r = client.get(f"{API}/mon-an", params={"nguyenLieu": "tôm"}).json()
    assert [m["tenMon"] for m in r["items"]] == ["Bánh bèo"]

    # món unverified không hiện trong danh sách và chi tiết
    all_items = client.get(f"{API}/mon-an", params={"size": 100}).json()
    assert all_items["total"] == 3
    assert client.get(f"{API}/mon-an/{du_lieu['bi_an'].idMonAn}").status_code == 404


def test_chi_tiet_mon(client, db_session):
    du_lieu = tao_du_lieu(db_session)
    r = client.get(f"{API}/mon-an/{du_lieu['bun_bo'].idMonAn}")
    assert r.status_code == 200
    d = r.json()
    assert d["danhMuc"]["tenDanhMuc"] == "Bún - Bánh canh - Mì"
    assert d["nguyenLieu"][0]["tenNguyenLieu"] == "Thịt bò"
    assert {t["tenSoThich"] for t in d["soThich"]} == {"Cay", "Món nước"}
    assert d["diaDiem"][0]["diaDiem"]["tenDiaDiem"] == "Bún bò O Phượng" and d["diaDiem"][0]["giaBan"] == 40000
    assert client.get(f"{API}/mon-an/{uuid.uuid4()}").json()["code"] == "MON_AN_NOT_FOUND"


def test_chi_tiet_tra_nhieu_anh(client, db_session):
    du_lieu = tao_du_lieu(db_session)
    mon, quan = du_lieu["bun_bo"], du_lieu["xa"]
    mon.hinhAnh = "https://img/bia.jpg"
    anh_repo.them_mon(db_session, mon.idMonAn, {"url": "https://img/1.jpg", "nguon": "site.vn"})
    anh_repo.them_mon(db_session, mon.idMonAn, {"url": "https://img/2.jpg"})
    anh_repo.them_dia_diem(db_session, quan.idDiaDiem, {"url": "https://img/q1.jpg"})
    db_session.commit()

    d = client.get(f"{API}/mon-an/{mon.idMonAn}").json()
    # ảnh bìa đứng đầu, sau đó là ảnh phụ theo thứ tự thu thập
    assert [a["url"] for a in d["anh"]] == ["https://img/bia.jpg", "https://img/1.jpg", "https://img/2.jpg"]
    assert d["anh"][1]["nguon"] == "site.vn"
    q = client.get(f"{API}/dia-diem/{quan.idDiaDiem}").json()
    assert [a["url"] for a in q["anh"]] == ["https://img/q1.jpg"]


def test_tim_dia_diem_theo_khoang_cach(client, db_session):
    du_lieu = tao_du_lieu(db_session)
    r = client.get(f"{API}/dia-diem", params={"viDo": 16.4637, "kinhDo": 107.5909, "banKinhKm": 5}).json()
    assert [d["tenDiaDiem"] for d in r["items"]] == ["Bún bò O Phượng", "Bánh bèo Bà Đỏ"]
    assert r["items"][0]["khoangCachKm"] < r["items"][1]["khoangCachKm"]

    r = client.get(f"{API}/dia-diem", params={"viDo": 16.4637, "kinhDo": 107.5909, "banKinhKm": 1}).json()
    assert r["total"] == 1
    assert client.get(f"{API}/dia-diem", params={"viDo": 16.4}).json()["code"] == "INVALID_LOCATION"

    r = client.get(f"{API}/dia-diem", params={"idMonAn": str(du_lieu["bun_bo"].idMonAn)}).json()
    assert [d["tenDiaDiem"] for d in r["items"]] == ["Bún bò O Phượng"]

    chi_tiet = client.get(f"{API}/dia-diem/{du_lieu['xa'].idDiaDiem}").json()
    assert chi_tiet["anhUrl"] == "https://lh5.googleusercontent.com/p_xa" and chi_tiet["monAn"][0]["monAn"]["tenMon"] == "Bánh bèo"



def test_so_thich_cua_toi(client, db_session, user_token):
    du_lieu = tao_du_lieu(db_session)
    h = auth_header(user_token)
    assert client.get(f"{API}/users/me/so-thich", headers=h).json() == []
    body = {"soThich": [{"idSoThich": str(du_lieu["cay"].idSoThich), "mucDo": 4}]}
    r = client.put(f"{API}/users/me/so-thich", json=body, headers=h)
    assert r.status_code == 200 and r.json()[0]["mucDo"] == 4

    body = {"soThich": [{"idSoThich": str(du_lieu["ngot"].idSoThich), "mucDo": 2}]}  # PUT thay toàn bộ
    assert [s["tenSoThich"] for s in client.put(f"{API}/users/me/so-thich", json=body, headers=h).json()] == ["Ngọt"]

    sai = {"soThich": [{"idSoThich": str(uuid.uuid4()), "mucDo": 3}]}
    assert client.put(f"{API}/users/me/so-thich", json=sai, headers=h).status_code == 404
    lap = {"soThich": [{"idSoThich": str(du_lieu["cay"].idSoThich)}] * 2}
    assert client.put(f"{API}/users/me/so-thich", json=lap, headers=h).status_code == 400
    qua_muc = {"soThich": [{"idSoThich": str(du_lieu["cay"].idSoThich), "mucDo": 6}]}
    assert client.put(f"{API}/users/me/so-thich", json=qua_muc, headers=h).status_code == 422
    assert client.get(f"{API}/users/me/so-thich").status_code == 401


def test_admin_thu_thap(client, admin_user, user_token, monkeypatch):
    goi = []
    monkeypatch.setattr(thu_thap_service, "chay", lambda loai, so_mon=None: goi.append((loai, so_mon)))
    assert client.post(f"{API}/admin/thu-thap", json={}, headers=auth_header(user_token)).status_code == 403

    token = client.post(
        f"{API}/auth/admin/login", json={"email": "admin@test.com", "matKhau": "adminpass123"}
    ).json()["accessToken"]
    r = client.post(f"{API}/admin/thu-thap", json={"loai": "mon_an", "soMon": 20}, headers=auth_header(token))
    assert r.status_code == 202 and goi == [("mon_an", 20)]
