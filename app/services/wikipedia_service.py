import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import ExternalServiceError

_API = "https://vi.wikipedia.org/w/api.php"
_KHOANG_NGHI_GIAY = 1.0
_DO_DAI_TOI_DA = 4000
_lan_goi_cuoi = 0.0


def _get(params: dict[str, Any]) -> dict[str, Any]:
    global _lan_goi_cuoi
    # Wikipedia yêu cầu User-Agent rõ ràng và không gọi dồn dập
    cho = _KHOANG_NGHI_GIAY - (time.monotonic() - _lan_goi_cuoi)
    if cho > 0:
        time.sleep(cho)
    try:
        r = httpx.get(
            _API,
            params={**params, "format": "json", "formatversion": 2},
            headers={"User-Agent": settings.WIKI_USER_AGENT},
            timeout=settings.HTTP_TIMEOUT_GIAY,
        )
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise ExternalServiceError(f"Wikipedia lỗi: {e}") from e
    finally:
        _lan_goi_cuoi = time.monotonic()


def tim_trang(tu_khoa: str, so_ket_qua: int = 5) -> list[dict[str, Any]]:
    """Trả về [{title, pageid}] theo độ liên quan."""
    data = _get({"action": "query", "list": "search", "srsearch": tu_khoa, "srlimit": so_ket_qua})
    return [{"title": s["title"], "pageid": s["pageid"]} for s in data.get("query", {}).get("search", [])]


def lay_noi_dung(pageid: int) -> dict[str, Any] | None:
    """Trả về {pageid, title, extract, url, anh} hoặc None nếu trang không tồn tại."""
    data = _get(
        {
            "action": "query",
            "pageids": pageid,
            "prop": "extracts|pageimages|info",
            "explaintext": 1,
            "exsectionformat": "plain",
            "piprop": "original|thumbnail",
            "pithumbsize": 800,
            "inprop": "url",
            "redirects": 1,
        }
    )
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return None
    p = pages[0]
    anh = (p.get("thumbnail") or p.get("original") or {}).get("source")
    return {
        "pageid": p["pageid"],
        "title": p["title"],
        "extract": (p.get("extract") or "")[:_DO_DAI_TOI_DA],
        "url": p.get("fullurl"),
        "anh": anh,
    }
