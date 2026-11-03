import uuid
from decimal import Decimal

from sqlalchemy import text

from app.db.base import Base
from app.models import DanhMucMonAn, DiaDiem, MonAn, MonAnDiaDiem, NguoiDung, SoThich, SoThichNguoiDung


def test_du_26_bang():
    # 24 bảng đồ án + AnhMonAn, AnhDiaDiem (migration 0004)
    assert len(Base.metadata.tables) == 26


def test_uuid_luu_char36_co_gach_noi(db_session):
    user = NguoiDung(email="u@test.com", matKhauMaHoa="x", hoTen="U")
    db_session.add(user)
    db_session.commit()

    raw = db_session.execute(text('SELECT "idNguoiDung" FROM "NguoiDung"')).scalar_one()
    assert raw == str(user.idNguoiDung) and len(raw) == 36
    assert db_session.get(NguoiDung, user.idNguoiDung) is user


def test_tao_mon_an_dia_diem_va_mac_dinh(db_session):
    dm = DanhMucMonAn(tenDanhMuc="Bún")
    db_session.add(dm)
    db_session.flush()
    mon = MonAn(
        idDanhMucMonAn=dm.idDanhMucMonAn, tenMon="Bún bò Huế", tenChuanHoa="bun bo hue", trangThai="active"
    )
    dd = DiaDiem(tenDiaDiem="Quán O Phượng", viDo=Decimal("16.4637"), trangThai="active")
    db_session.add_all([mon, dd])
    db_session.flush()
    link = MonAnDiaDiem(idMonAn=mon.idMonAn, idDiaDiem=dd.idDiaDiem)
    db_session.add(link)
    db_session.commit()

    assert isinstance(link.idMonAnDiaDiem, uuid.UUID)
    assert link.laMonDacTrung is False
    assert mon.ngayTao is not None


def test_so_thich_nguoi_dung_muc_do_mac_dinh(db_session):
    user = NguoiDung(email="s@test.com", matKhauMaHoa="x", hoTen="S")
    st = SoThich(loai="vi", tenSoThich="Cay")
    db_session.add_all([user, st])
    db_session.flush()
    stnd = SoThichNguoiDung(idNguoiDung=user.idNguoiDung, idSoThich=st.idSoThich)
    db_session.add(stnd)
    db_session.commit()
    assert stnd.mucDo == 3
