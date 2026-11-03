from datetime import datetime, timedelta

from app.core.constants import LoaiGoiY
from app.models import GoiY, NguCanh
from app.services.ngu_canh_service import TZ_VN
from tests.conftest import auth_header
from tests.du_lieu_mau import tao_du_lieu
from tests.test_admin import _admin_token

URL = "/api/v1/admin/thong-ke"


def _luot_goi_y(db, user_id, luc: datetime, mons: list) -> None:
    nc = NguCanh(idNguoiDung=user_id, thoiDiem=luc, laNgayRam=False)
    db.add(nc)
    db.flush()
    db.add_all(
        GoiY(idNguCanh=nc.idNguCanh, idNguoiDung=user_id, idMonAn=m.idMonAn, loaiGoiY=LoaiGoiY.MON_AN.value, ngayTao=luc)
        for m in mons
    )
    db.commit()


def test_thong_ke_tong_quan(client, db_session, user_token, admin_user):
    d = tao_du_lieu(db_session)
    uid = client.get("/api/v1/users/me", headers=auth_header(user_token)).json()["idNguoiDung"]
    now = datetime.now(TZ_VN).replace(tzinfo=None)
    _luot_goi_y(db_session, uid, now, [d["bun_bo"], d["banh_beo"]])
    _luot_goi_y(db_session, uid, now, [d["bun_bo"]])
    _luot_goi_y(db_session, uid, now - timedelta(days=2), [d["bun_bo"], d["che_chay"]])
    _luot_goi_y(db_session, uid, now - timedelta(days=30), [d["che_chay"]] * 5)  # ngoài kỳ 7 ngày
    client.post(
        "/api/v1/bao-cao", json={"idDiaDiem": str(d["gan"].idDiaDiem), "lyDo": "Sai"}, headers=auth_header(user_token)
    )

    r = client.get(URL, headers=auth_header(_admin_token(client)))
    assert r.status_code == 200, r.text
    data = r.json()
    tq = data["tongQuan"]
    # admin không tính là người dùng; món "chưa xác minh" không tính
    assert (tq["nguoiDung"], tq["nguoiDungMoi"], tq["monAn"], tq["diaDiem"]) == (1, 1, 3, 2)
    assert tq["baoCaoChoXuLy"] == 1 and tq["luotGoiY"] == 3

    theo_ngay = data["goiYTheoNgay"]
    assert len(theo_ngay) == 7 and theo_ngay[-1] == {"ngay": now.date().isoformat(), "soLuot": 2}
    assert theo_ngay[-3]["soLuot"] == 1 and sum(x["soLuot"] for x in theo_ngay) == 3
    assert [(m["tenMon"], m["soLanGoiY"]) for m in data["topMonGoiY"]] == [
        ("Bún bò Huế", 3),
        ("Bánh bèo", 1),
        ("Chè bắp", 1),
    ]

    # kỳ 90 ngày tính cả lượt 30 ngày trước
    data = client.get(URL, params={"soNgay": 90}, headers=auth_header(_admin_token(client))).json()
    assert data["tongQuan"]["luotGoiY"] == 4 and data["topMonGoiY"][0]["tenMon"] == "Chè bắp"


def test_thong_ke_chi_admin(client, user_token, admin_user):
    assert client.get(URL, headers=auth_header(user_token)).status_code == 403
    assert client.get(URL, params={"soNgay": 0}, headers=auth_header(_admin_token(client))).status_code == 422
