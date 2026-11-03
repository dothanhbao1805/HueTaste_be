from sqlalchemy import select

from app.models import DiaDiem, MonAnDiaDiem
from app.repositories import bao_cao_repo
from app.services import serper_service, thu_thap_service
from tests.conftest import auth_header
from tests.du_lieu_mau import tao_du_lieu
from tests.test_admin import _admin_token

URL = "/api/v1/bao-cao"
URL_ADMIN = "/api/v1/admin/bao-cao"


def _gui(client, h, d, mon=("banh_beo",), **kw):
    body = {"idDiaDiem": str(d["gan"].idDiaDiem), "lyDo": "Sai thực đơn", "idMonAn": [str(d[m].idMonAn) for m in mon]}
    return client.post(URL, json={**body, **kw}, headers=h)


def _id_link(db_session, mon, quan):
    return db_session.scalar(
        select(MonAnDiaDiem.idMonAnDiaDiem).where(
            MonAnDiaDiem.idMonAn == mon.idMonAn, MonAnDiaDiem.idDiaDiem == quan.idDiaDiem
        )
    )


def test_user_gui_va_xem_bao_cao(client, db_session, user_token):
    d = tao_du_lieu(db_session)
    h = auth_header(user_token)
    r = _gui(client, h, d, mon=("banh_beo", "banh_beo"), moTa="Quán không bán bánh bèo")
    assert r.status_code == 201, r.text
    bc = r.json()
    assert bc["trangThai"] == "CHO_XU_LY" and bc["nguoiBaoCao"] is None
    assert [(c["monAn"]["tenMon"], c["ketQuaXuLy"]) for c in bc["chiTiet"]] == [("Bánh bèo", "CHO_XU_LY")]

    # đang có báo cáo chờ cho quán này -> không gửi tiếp
    r = _gui(client, h, d)
    assert r.status_code == 409 and r.json()["code"] == "BAO_CAO_DANG_CHO"
    assert client.get("/api/v1/users/me/bao-cao", headers=h).json()["total"] == 1


def test_gui_bao_cao_validate(client, db_session, user_token):
    d = tao_du_lieu(db_session)
    h = auth_header(user_token)
    # chè bắp không có ở quán "gan"
    r = _gui(client, h, d, mon=("che_chay",))
    assert r.status_code == 400 and r.json()["code"] == "MON_KHONG_THUOC_QUAN"
    assert _gui(client, h, d, lyDo="").status_code == 422
    assert _gui(client, {}, d).status_code == 401
    # báo cáo chỉ về quán, không kèm món
    assert _gui(client, h, d, mon=()).status_code == 201


def test_admin_xu_ly_go_mon_va_an_quan(client, db_session, user_token, admin_user):
    d = tao_du_lieu(db_session)
    bc = _gui(client, auth_header(user_token), d, mon=("banh_beo", "bun_bo")).json()
    ha = auth_header(_admin_token(client))

    ds = client.get(URL_ADMIN, params={"trangThai": "CHO_XU_LY"}, headers=ha).json()
    assert ds["total"] == 1 and ds["items"][0]["nguoiBaoCao"]["email"] == "user@test.com"
    ct = {c["monAn"]["tenMon"]: c["idChiTietBaoCao"] for c in ds["items"][0]["chiTiet"]}

    # thiếu kết quả cho 1 món -> 400
    thieu = {"chiTiet": [{"idChiTietBaoCao": ct["Bánh bèo"], "ketQua": "VI_PHAM"}]}
    r = client.post(f"{URL_ADMIN}/{bc['idBaoCao']}/xu-ly", json=thieu, headers=ha)
    assert r.status_code == 400 and r.json()["code"] == "KET_QUA_KHONG_KHOP"

    body = {
        "chiTiet": [
            {"idChiTietBaoCao": ct["Bánh bèo"], "ketQua": "VI_PHAM"},
            {"idChiTietBaoCao": ct["Bún bò Huế"], "ketQua": "KHONG_VI_PHAM"},
        ],
        "anQuan": True,
        "ketQuaXuLy": "Đã gỡ bánh bèo và ẩn quán",
    }
    r = client.post(f"{URL_ADMIN}/{bc['idBaoCao']}/xu-ly", json=body, headers=ha)
    assert r.status_code == 200, r.text
    assert r.json()["trangThai"] == "DA_XU_LY" and r.json()["xuLyLuc"] and r.json()["diaDiem"]["trangThai"] == "hidden"

    db_session.expire_all()
    assert _id_link(db_session, d["banh_beo"], d["gan"]) is None  # đã gỡ
    assert _id_link(db_session, d["bun_bo"], d["gan"]) is not None  # giữ nguyên
    assert db_session.get(DiaDiem, d["gan"].idDiaDiem).trangThai == "hidden"
    assert client.get(f"/api/v1/dia-diem/{d['gan'].idDiaDiem}").status_code == 404

    r = client.post(f"{URL_ADMIN}/{bc['idBaoCao']}/xu-ly", json=body, headers=ha)
    assert r.status_code == 409 and r.json()["code"] == "BAO_CAO_DA_XU_LY"
    # người báo cáo thấy kết quả
    cua_toi = client.get("/api/v1/users/me/bao-cao", headers=auth_header(user_token)).json()["items"][0]
    assert cua_toi["ketQuaXuLy"] == "Đã gỡ bánh bèo và ẩn quán"
    assert {c["ketQuaXuLy"] for c in cua_toi["chiTiet"]} == {"VI_PHAM", "KHONG_VI_PHAM"}


def test_pipeline_khong_gan_lai_mon_vi_pham(client, db_session, user_token, admin_user):
    d = tao_du_lieu(db_session)
    bc = _gui(client, auth_header(user_token), d).json()
    ha = auth_header(_admin_token(client))
    body = {"chiTiet": [{"idChiTietBaoCao": bc["chiTiet"][0]["idChiTietBaoCao"], "ketQua": "VI_PHAM"}]}
    assert client.post(f"{URL_ADMIN}/{bc['idBaoCao']}/xu-ly", json=body, headers=ha).status_code == 200
    assert bao_cao_repo.mon_bi_go(db_session, d["banh_beo"].idMonAn, d["gan"].idDiaDiem)

    p = serper_service.chuan_hoa(
        {"placeId": "p_gan", "title": "Bún bò O Phượng", "latitude": 16.4650, "longitude": 107.5920, "rating": 4.7}
    )
    thu_thap_service._luu_quan(db_session, d["banh_beo"], p, 20)
    thu_thap_service._luu_quan(db_session, d["che_chay"], p, 20)
    db_session.commit()
    assert _id_link(db_session, d["banh_beo"], d["gan"]) is None
    assert _id_link(db_session, d["che_chay"], d["gan"]) is not None  # món khác vẫn gắn bình thường


def test_admin_bao_cao_quyen_va_404(client, user_token, admin_user):
    assert client.get(URL_ADMIN, headers=auth_header(user_token)).status_code == 403
    ha = auth_header(_admin_token(client))
    r = client.get(f"{URL_ADMIN}/00000000-0000-0000-0000-000000000000", headers=ha)
    assert r.status_code == 404 and r.json()["code"] == "BAO_CAO_NOT_FOUND"
