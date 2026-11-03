from app.services import llm_service, thu_thap_service
from tests.conftest import auth_header
from tests.du_lieu_mau import tao_du_lieu
from tests.test_admin import _admin_token

URL = "/api/v1/admin/danh-muc"


def test_admin_crud_danh_muc(client, admin_user):
    h = auth_header(_admin_token(client))
    r = client.post(URL, json={"tenDanhMuc": " Đồ uống ", "moTa": "Nước, sinh tố"}, headers=h)
    assert r.status_code == 201 and r.json()["tenDanhMuc"] == "Đồ uống" and r.json()["soMon"] == 0
    id_dm = r.json()["idDanhMucMonAn"]

    # trùng tên không phân biệt hoa thường
    r = client.post(URL, json={"tenDanhMuc": "đồ UỐNG"}, headers=h)
    assert r.status_code == 409 and r.json()["code"] == "DANH_MUC_EXISTS"

    r = client.patch(f"{URL}/{id_dm}", json={"tenDanhMuc": "Đồ uống Huế"}, headers=h)
    assert r.status_code == 200 and r.json()["tenDanhMuc"] == "Đồ uống Huế" and r.json()["moTa"] == "Nước, sinh tố"
    assert [d["tenDanhMuc"] for d in client.get("/api/v1/danh-muc").json()] == ["Đồ uống Huế"]

    assert client.delete(f"{URL}/{id_dm}", headers=h).status_code == 200
    r = client.delete(f"{URL}/{id_dm}", headers=h)
    assert r.status_code == 404 and r.json()["code"] == "DANH_MUC_NOT_FOUND"


def test_khong_xoa_danh_muc_con_mon_va_dem_so_mon(client, db_session, admin_user):
    du_lieu = tao_du_lieu(db_session)
    h = auth_header(_admin_token(client))
    ds = {d["tenDanhMuc"]: d for d in client.get(URL, headers=h).json()}
    assert ds["Bún - Bánh canh - Mì"]["soMon"] == 2  # tính cả món chưa xác minh
    r = client.delete(f"{URL}/{du_lieu['bun_bo'].idDanhMucMonAn}", headers=h)
    assert r.status_code == 409 and r.json()["code"] == "DANH_MUC_IN_USE"
    r = client.patch(f"{URL}/{du_lieu['bun_bo'].idDanhMucMonAn}", json={"tenDanhMuc": "Bánh Huế"}, headers=h)
    assert r.status_code == 409


def test_danh_muc_chi_admin(client, user_token):
    assert client.get(URL).status_code == 401
    assert client.post(URL, json={"tenDanhMuc": "X"}, headers=auth_header(user_token)).status_code == 403


def test_pipeline_dung_danh_muc_trong_db(db_session, monkeypatch, client, admin_user):
    h = auth_header(_admin_token(client))
    client.post(URL, json={"tenDanhMuc": "Đồ uống"}, headers=h)
    schemas = []

    def fake_llm(prompt, schema, **_):
        schemas.append(schema)
        return []

    monkeypatch.setattr(llm_service, "generate_json", fake_llm)
    thu_thap_service.thu_thap_mon_an(db_session, 5)
    assert schemas[0]["items"]["properties"]["danhMuc"]["enum"] == ["Đồ uống"]
