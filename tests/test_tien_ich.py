from datetime import date

import pytest

from app.core.am_lich import duong_sang_am, la_ngay_ram
from app.core.chuan_hoa import chuan_hoa_ten, do_tuong_dong
from app.core.constants import Buoi, ThoiTiet
from app.core.geo import bounding_box, haversine_km
from app.services.ngu_canh_service import buoi_theo_gio
from app.services.thoi_tiet_service import quy_doi_thoi_tiet


@pytest.mark.parametrize(
    "duong, am",
    [
        (date(2024, 2, 10), (1, 1, 2024, False)),  # Tết Giáp Thìn
        (date(2025, 1, 29), (1, 1, 2025, False)),  # Tết Ất Tỵ
        (date(2026, 2, 17), (1, 1, 2026, False)),  # Tết Bính Ngọ
        (date(2024, 9, 17), (15, 8, 2024, False)),  # Trung thu
        (date(2023, 3, 22), (1, 2, 2023, True)),  # mùng 1 tháng 2 nhuận
    ],
)
def test_duong_sang_am(duong, am):
    assert duong_sang_am(duong) == am


def test_la_ngay_ram():
    assert la_ngay_ram(date(2024, 9, 17))  # rằm
    assert la_ngay_ram(date(2024, 2, 10))  # mùng 1
    assert not la_ngay_ram(date(2024, 9, 18))


def test_chuan_hoa_ten():
    assert chuan_hoa_ten("Bún Bò  Huế!") == "bun bo hue"
    assert chuan_hoa_ten("Đậu hũ") == "dau hu"
    assert chuan_hoa_ten("bún bò huế") == chuan_hoa_ten("BÚN BÒ HUẾ")
    assert do_tuong_dong("Bún bò Huế", "bun bo hue") == 1.0


def test_haversine_va_bounding_box():
    assert haversine_km(16.4637, 107.5909, 16.4637, 107.5909) == 0
    assert 75 < haversine_km(16.4637, 107.5909, 16.0544, 108.2022) < 85  # Huế - Đà Nẵng
    vi_min, vi_max, kinh_min, kinh_max = bounding_box(16.46, 107.59, 5)
    assert vi_min < 16.46 < vi_max and kinh_min < 107.59 < kinh_max


def test_quy_doi_thoi_tiet():
    assert quy_doi_thoi_tiet(25, 61) == ThoiTiet.MUA
    assert quy_doi_thoi_tiet(25, 0, 1.0) == ThoiTiet.MUA
    assert quy_doi_thoi_tiet(19, 1) == ThoiTiet.LANH
    assert quy_doi_thoi_tiet(34, 0) == ThoiTiet.NONG
    assert quy_doi_thoi_tiet(27, 2) == ThoiTiet.MAT


def test_buoi_theo_gio():
    assert buoi_theo_gio(7) == Buoi.SANG
    assert buoi_theo_gio(12) == Buoi.TRUA
    assert buoi_theo_gio(15) == Buoi.CHIEU
    assert buoi_theo_gio(19) == Buoi.TOI
    assert buoi_theo_gio(23) == Buoi.KHUYA
