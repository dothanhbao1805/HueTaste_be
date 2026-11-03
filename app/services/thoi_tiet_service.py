import logging
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.constants import ThoiTiet

logger = logging.getLogger(__name__)

_URL = "https://api.open-meteo.com/v1/forecast"
_CACHE_GIAY = 15 * 60
_cache: dict[tuple[float, float], tuple[float, dict[str, Any]]] = {}

# Mã WMO có mưa: mưa phùn, mưa, mưa rào, dông
_MA_MUA = set(range(51, 68)) | set(range(80, 83)) | set(range(95, 100))


def quy_doi_thoi_tiet(nhiet_do: float, weather_code: int, luong_mua_mm: float = 0.0) -> ThoiTiet:
    if weather_code in _MA_MUA or luong_mua_mm >= 0.2:
        return ThoiTiet.MUA
    if nhiet_do < 22:
        return ThoiTiet.LANH
    if nhiet_do > 31:
        return ThoiTiet.NONG
    return ThoiTiet.MAT


def lay_thoi_tiet(vi_do: float, kinh_do: float) -> dict[str, Any] | None:
    """{nhietDo, thoiTiet} hiện tại; None nếu lỗi để gợi ý vẫn chạy được không có thời tiết."""
    khoa = (round(vi_do, 2), round(kinh_do, 2))
    da_luu = _cache.get(khoa)
    if da_luu and time.monotonic() - da_luu[0] < _CACHE_GIAY:
        return da_luu[1]
    try:
        r = httpx.get(
            _URL,
            params={
                "latitude": vi_do,
                "longitude": kinh_do,
                "current": "temperature_2m,weather_code,precipitation",
                "timezone": "Asia/Ho_Chi_Minh",
            },
            timeout=min(settings.HTTP_TIMEOUT_GIAY, 5.0),
        )
        r.raise_for_status()
        cur = r.json()["current"]
        nhiet_do = float(cur["temperature_2m"])
        ket_qua = {
            "nhietDo": nhiet_do,
            "thoiTiet": quy_doi_thoi_tiet(
                nhiet_do, int(cur["weather_code"]), float(cur.get("precipitation") or 0)
            ).value,
        }
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as e:
        logger.warning("Không lấy được thời tiết: %s", e)
        return None
    _cache[khoa] = (time.monotonic(), ket_qua)
    return ket_qua
