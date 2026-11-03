import uuid
from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.models import GoiY, MonAn, NguCanh, NhuCauTheoNgay
from app.services import goi_y_service as gy
from app.services import ngu_canh_service, thoi_tiet_service
from tests.conftest import auth_header
from tests.du_lieu_mau import tao_du_lieu

ID_CAY, ID_NUOC, ID_NGOT, ID_CHAY = (uuid.uuid4() for _ in range(4))


def _mon(ten, buoi=(), thoi_tiet=(), gia=None, tags=None, chay=False, yeu_thich=False, danh_muc=None):
    return gy.DuLieuMon(
        mon=MonAn(idMonAn=uuid.uuid4(), tenMon=ten, idDanhMucMonAn=danh_muc or uuid.uuid4()),
        buoi=set(buoi),
        thoi_tiet=set(thoi_tiet),
        gia=gia,
        tags=tags or {},
        che_do={ID_CHAY} if chay else set(),
        danh_gia=None,
        la_chay=chay,
        la_yeu_thich=yeu_thich,
    )


def _nc(**kw):
    base = dict(buoi="sang", bua_an=None, thoi_tiet=None, nhiet_do=None, la_ngay_ram=False,
                ngan_sach=None, ghi_chu=None, so_thich={})
    return gy.NguCanhCham(**{**base, **kw})


BUN_BO = dict(buoi=("sang",), thoi_tiet=("lanh", "mua"), gia=40000,
              tags={ID_CAY: ("vi", "Cay", 0.9), ID_NUOC: ("kieu", "Món nước", 1.0)})


def test_troi_lanh_buoi_sang_uu_tien_mon_nuoc():
    bun_bo = gy.cham_diem_mon(_mon("Bún bò", **BUN_BO), _nc(thoi_tiet="lanh", nhiet_do=19))
    che = gy.cham_diem_mon(_mon("Chè", buoi=("chieu",), thoi_tiet=("nong",)), _nc(thoi_tiet="lanh"))
    assert bun_bo.tong > che.tong
    assert "Hợp bữa sáng" in gy.ly_do_mon(bun_bo) and "se lạnh 19°C" in gy.ly_do_mon(bun_bo)


def test_ngay_ram_uu_tien_mon_chay():
    chay = gy.cham_diem_mon(_mon("Cơm chay", buoi=("sang",), chay=True), _nc(la_ngay_ram=True))
    man = gy.cham_diem_mon(_mon("Bún bò", buoi=("sang",)), _nc(la_ngay_ram=True))
    assert chay.thanh_phan["nguCanh"] > man.thanh_phan["nguCanh"]
    assert "món chay" in gy.ly_do_mon(chay)


def test_so_thich_va_ngan_sach():
    nc = _nc(so_thich={ID_CAY: 5}, ngan_sach=50000)
    bun_bo = gy.cham_diem_mon(_mon("Bún bò", **BUN_BO), nc)
    assert bun_bo.thanh_phan["soThich"] == pytest.approx(0.9)
    assert bun_bo.thanh_phan["nganSach"] == 1.0
    assert "Đúng khẩu vị cay bạn thích" in gy.ly_do_mon(bun_bo)
    assert gy.cham_ngan_sach(60000, 50000)[0] == pytest.approx(0.6)
    assert gy.cham_ngan_sach(80000, 50000)[0] == 0.0
    assert gy.cham_ngan_sach(None, 50000)[0] == 0.5


def test_ghi_chu_it_cay_va_yeu_thich():
    bun_bo = _mon("Bún bò", **BUN_BO)
    it_cay, _ = gy.cham_ghi_chu(bun_bo, "Ít cay")
    thich_cay, ly_do = gy.cham_ghi_chu(bun_bo, "thích ăn cay")
    assert it_cay < 0.5 < thich_cay and "Đúng ý bạn: cay" in ly_do
    # 2 cụm cùng chỉ "Món nước" chỉ được cộng 1 lần
    mot, _ = gy.cham_ghi_chu(bun_bo, "nước dùng")
    hai, _ = gy.cham_ghi_chu(bun_bo, "nước dùng ấm nóng")
    assert mot == hai == pytest.approx(0.75)
    diem, ly_do = gy.cham_ghi_chu(_mon("Bánh", yeu_thich=True), None)
    assert diem == pytest.approx(0.8) and "Món bạn đã yêu thích" in ly_do


def test_loc_che_do_an_va_da_dang_danh_muc():
    chay, man = _mon("Chè", chay=True), _mon("Bún bò")
    assert gy.loc_che_do_an([chay, man], {ID_CHAY}) == [chay]
    assert gy.loc_che_do_an([chay, man], set()) == [chay, man]

    dm_bun = uuid.uuid4()
    ds = [gy.DiemMon(_mon(f"Bún {i}", danh_muc=dm_bun), 0.9 - i * 0.01, {}) for i in range(4)]
    ds.append(gy.DiemMon(_mon("Bánh bèo"), 0.5, {}))
    top = gy.chon_top_mon(ds, 3)
    assert [d.du_lieu.mon.tenMon for d in top] == ["Bún 0", "Bún 1", "Bánh bèo"]


# ---------------------------------------------------------------- API


@pytest.fixture()
def co_dinh_ngu_canh(monkeypatch):
    monkeypatch.setattr(thoi_tiet_service, "lay_thoi_tiet", lambda *_: {"nhietDo": 20.0, "thoiTiet": "lanh"})
    monkeypatch.setattr(ngu_canh_service, "la_ngay_ram", lambda d: False)


def test_api_goi_y(client, db_session, user_token, co_dinh_ngu_canh):
    tao_du_lieu(db_session)
    h = auth_header(user_token)
    cay = client.get("/api/v1/so-thich").json()
    id_cay = next(s["idSoThich"] for s in cay if s["tenSoThich"] == "Cay")
    assert client.put("/api/v1/users/me/so-thich", json={"soThich": [{"idSoThich": id_cay, "mucDo": 5}]}, headers=h).status_code == 200

    body = {"viDo": 16.4637, "kinhDo": 107.5909, "buaAn": "sang", "nganSach": 50000, "ghiChu": "nước dùng nóng"}
    r = client.post("/api/v1/goi-y", json=body, headers=h)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["nguCanh"]["buoiTrongNgay"] == "sang" and data["nguCanh"]["thoiTiet"] == "lanh"
    ten_mon = [m["monAn"]["tenMon"] for m in data["monAn"]]
    assert ten_mon[0] == "Bún bò Huế" and "Món chưa xác minh" not in ten_mon
    assert data["monAn"][0]["thuHang"] == 1 and 0 < data["monAn"][0]["diemSo"] <= 1
    assert "cay" in data["monAn"][0]["lyDoGiaiThich"]
    quan = data["diaDiem"]
    assert quan[0]["diaDiem"]["tenDiaDiem"] == "Bún bò O Phượng"
    assert quan[0]["diaDiem"]["khoangCachKm"] < 1 and quan[0]["monLienQuan"][0]["tenMon"] == "Bún bò Huế"

    # đã lưu ngữ cảnh, nhu cầu và từng dòng gợi ý
    assert db_session.scalar(select(func.count()).select_from(NguCanh)) == 1
    assert db_session.scalar(select(func.count()).select_from(NhuCauTheoNgay)) == 1
    assert db_session.scalar(select(func.count()).select_from(GoiY)) == len(data["monAn"]) + len(quan)


def test_api_goi_y_che_do_chay(client, db_session, user_token, co_dinh_ngu_canh):
    du_lieu = tao_du_lieu(db_session)
    h = auth_header(user_token)
    r = client.put(
        "/api/v1/users/me/che-do-an", json={"cheDoAn": [{"idCheDoAn": str(du_lieu["chay"].idCheDoAn)}]}, headers=h
    )
    assert r.status_code == 200 and r.json()[0]["tenCheDo"] == "Ăn chay"
    data = client.post("/api/v1/goi-y", json={}, headers=h).json()
    assert [m["monAn"]["tenMon"] for m in data["monAn"]] == ["Chè bắp"]


def test_api_goi_y_validate_va_auth(client, user_token):
    assert client.post("/api/v1/goi-y", json={}).status_code == 401
    r = client.post("/api/v1/goi-y", json={"buaAn": "an_trua"}, headers=auth_header(user_token))
    assert r.status_code == 422


def test_loc_nguyen_lieu_tranh():
    bun_bo, che = _mon("Bún bò"), _mon("Chè")
    assert gy.loc_nguyen_lieu_tranh([bun_bo, che], {bun_bo.mon.idMonAn}) == [che]
    assert gy.loc_nguyen_lieu_tranh([bun_bo, che], set()) == [bun_bo, che]


def test_api_goi_y_tranh_nguyen_lieu(client, db_session, user_token, co_dinh_ngu_canh):
    du_lieu = tao_du_lieu(db_session)
    h = auth_header(user_token)
    id_bo = str(du_lieu["thit_bo"].idNguyenLieu)
    data = client.post("/api/v1/goi-y", json={"buaAn": "sang", "nguyenLieuTranh": [id_bo]}, headers=h).json()
    assert "Bún bò Huế" not in [m["monAn"]["tenMon"] for m in data["monAn"]]

    # lần sau không gửi: dùng danh sách đã lưu trong nhu cầu của bữa sáng
    data = client.post("/api/v1/goi-y", json={"buaAn": "sang"}, headers=h).json()
    ten_mon = [m["monAn"]["tenMon"] for m in data["monAn"]]
    assert "Bún bò Huế" not in ten_mon and "Bánh bèo" in ten_mon


def test_api_goi_y_chon_bua_theo_gio_an(client, db_session, user_token, co_dinh_ngu_canh):
    tao_du_lieu(db_session)
    h = auth_header(user_token)
    bay_gio = datetime.now(ngu_canh_service.TZ_VN).strftime("%H:%M")
    # đặt bữa "khuya" đúng giờ hiện tại để khác khung giờ mặc định (trừ khi đang là khuya thật)
    bua = "an_vat" if ngu_canh_service.buoi_theo_gio(datetime.now(ngu_canh_service.TZ_VN).hour) == "khuya" else "khuya"
    client.put("/api/v1/users/me/nhu-cau", json={"buaAn": bua, "gioAn": bay_gio, "nganSach": 20000}, headers=h)
    data = client.post("/api/v1/goi-y", json={}, headers=h).json()
    nc = db_session.scalar(select(NguCanh))
    luu = db_session.get(NhuCauTheoNgay, nc.idNhuCauTheoNgay)
    assert luu.buaAn == bua and int(luu.nganSach) == 20000
    if bua == "khuya":
        assert data["nguCanh"]["buoiTrongNgay"] == "khuya"
