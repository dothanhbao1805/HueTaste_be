from sqlalchemy import func, select

from app.models import DanhSachYeuThich
from tests.conftest import auth_header
from tests.du_lieu_mau import tao_du_lieu

URL = "/api/v1/users/me/yeu-thich"


def test_them_list_xoa_yeu_thich(client, db_session, user_token):
    d = tao_du_lieu(db_session)
    h = auth_header(user_token)
    id_mon, id_quan = str(d["bun_bo"].idMonAn), str(d["gan"].idDiaDiem)

    assert client.post(URL, json={"idMonAn": id_mon}, headers=h).status_code == 201
    assert client.post(URL, json={"idMonAn": id_mon}, headers=h).status_code == 201  # lặp lại không lỗi
    assert client.post(URL, json={"idDiaDiem": id_quan}, headers=h).status_code == 201
    assert db_session.scalar(select(func.count()).select_from(DanhSachYeuThich)) == 2

    data = client.get(URL, headers=h).json()
    assert [m["tenMon"] for m in data["monAn"]] == ["Bún bò Huế"]
    assert [q["tenDiaDiem"] for q in data["diaDiem"]] == ["Bún bò O Phượng"]
    assert client.get(URL, params={"loai": "dia_diem"}, headers=h).json()["monAn"] == []

    # cờ daYeuThich trên trang chi tiết: có token mới biết, khách luôn false
    assert client.get(f"/api/v1/mon-an/{id_mon}", headers=h).json()["daYeuThich"] is True
    assert client.get(f"/api/v1/mon-an/{id_mon}").json()["daYeuThich"] is False
    assert client.get(f"/api/v1/dia-diem/{id_quan}", headers=h).json()["daYeuThich"] is True
    assert client.get(f"/api/v1/mon-an/{d['banh_beo'].idMonAn}", headers=h).json()["daYeuThich"] is False

    assert client.delete(f"{URL}/mon-an/{id_mon}", headers=h).status_code == 200
    r = client.delete(f"{URL}/mon-an/{id_mon}", headers=h)
    assert r.status_code == 404 and r.json()["code"] == "YEU_THICH_NOT_FOUND"
    assert client.delete(f"{URL}/dia-diem/{id_quan}", headers=h).status_code == 200
    assert client.get(URL, headers=h).json() == {"monAn": [], "diaDiem": []}


def test_yeu_thich_validate(client, db_session, user_token):
    d = tao_du_lieu(db_session)
    h = auth_header(user_token)
    assert client.post(URL, json={}, headers=h).status_code == 422
    both = {"idMonAn": str(d["bun_bo"].idMonAn), "idDiaDiem": str(d["gan"].idDiaDiem)}
    assert client.post(URL, json=both, headers=h).status_code == 422
    # món chưa xác minh không hiển thị nên cũng không yêu thích được
    r = client.post(URL, json={"idMonAn": str(d["bi_an"].idMonAn)}, headers=h)
    assert r.status_code == 404 and r.json()["code"] == "MON_AN_NOT_FOUND"
    assert client.get(URL).status_code == 401
    # token hỏng ở endpoint công khai -> coi như khách, không 401
    assert client.get(f"/api/v1/mon-an/{d['bun_bo'].idMonAn}", headers=auth_header("sai")).status_code == 200
