"""Tìm quán qua Serper (serper.dev): kết quả Google Maps dạng JSON, không cần billing Google Cloud.

Serper không công bố schema chi tiết nên parse mềm dẻo: id lấy placeId -> cid -> fid,
giờ mở cửa nhận cả dict lẫn list.
"""
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import ExternalServiceError

_MAPS_URL = "https://google.serper.dev/maps"
_IMAGES_URL = "https://google.serper.dev/images"
_ZOOM = 14  # ~ vài km quanh tâm, đủ cho nội thành Huế


def _key() -> str:
    if not settings.SERPER_API_KEY:
        raise ExternalServiceError("Chưa cấu hình SERPER_API_KEY", "SERPER_NOT_CONFIGURED")
    return settings.SERPER_API_KEY


def tim_quan(tu_khoa: str, vi_do: float, kinh_do: float, so_ket_qua: int = 10) -> list[dict[str, Any]]:
    body = {"q": tu_khoa, "ll": f"@{vi_do},{kinh_do},{_ZOOM}z", "gl": "vn", "hl": "vi"}
    try:
        r = httpx.post(
            _MAPS_URL,
            json=body,
            headers={"X-API-KEY": _key(), "Content-Type": "application/json"},
            timeout=settings.HTTP_TIMEOUT_GIAY,
        )
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise ExternalServiceError(f"Serper lỗi: {e}") from e
    return [chuan_hoa(p) for p in r.json().get("places", [])[:so_ket_qua]]


def tim_anh(tu_khoa: str, so_anh: int = 10) -> list[dict[str, Any]]:
    """Google Images qua Serper: trả danh sách đã chuẩn hoá bởi chuan_hoa_anh."""
    body = {"q": tu_khoa, "gl": "vn", "hl": "vi", "num": so_anh}
    try:
        r = httpx.post(
            _IMAGES_URL,
            json=body,
            headers={"X-API-KEY": _key(), "Content-Type": "application/json"},
            timeout=settings.HTTP_TIMEOUT_GIAY,
        )
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise ExternalServiceError(f"Serper lỗi: {e}") from e
    return [a for a in (chuan_hoa_anh(x) for x in r.json().get("images", [])[:so_anh]) if a["url"]]


def chuan_hoa_anh(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "url": p.get("imageUrl"),
        "thumbnail": p.get("thumbnailUrl"),
        "nguon": p.get("source") or p.get("domain"),
        "tieuDe": p.get("title"),
        "rong": p.get("imageWidth"),
        "cao": p.get("imageHeight"),
    }


def _muc_gia(v: Any) -> int | None:
    # Google Maps hiển thị mức giá bằng ký hiệu lặp: "$$", "₫₫"...
    if isinstance(v, str):
        v = v.strip()
        if v and len(set(v)) == 1 and len(v) <= 4:
            return len(v)
    return None


def _gio_mo_cua(v: Any) -> list[str] | None:
    if isinstance(v, dict):
        return [f"{ngay}: {gio}" for ngay, gio in v.items()] or None
    if isinstance(v, list):
        return [str(x) for x in v] or None
    return None


def chuan_hoa(p: dict[str, Any]) -> dict[str, Any]:
    pid = p.get("placeId") or p.get("cid") or p.get("fid")
    return {
        "id": str(pid) if pid else None,
        "ten": p.get("title"),
        "diaChi": p.get("address"),
        "viDo": p.get("latitude"),
        "kinhDo": p.get("longitude"),
        "rating": p.get("rating"),
        "soDanhGia": p.get("ratingCount"),
        "mucGia": _muc_gia(p.get("priceLevel")),
        "soDienThoai": p.get("phoneNumber"),
        "gioMoCua": _gio_mo_cua(p.get("openingHours")),
        "anh": p.get("thumbnailUrl"),  # URL ảnh công khai, app dùng thẳng
    }
