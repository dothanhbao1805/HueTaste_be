import base64
import json
import logging
import re
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_MA_THU_LAI = {429, 500, 503}
_NGHI_MODEL_QUA_TAI_GIAY = 10 * 60
_qua_tai_den: dict[str, float] = {}  # model -> thời điểm (monotonic) được thử lại


def _cac_model() -> list[str]:
    du_phong = [m.strip() for m in settings.GEMINI_MODEL_DU_PHONG.split(",") if m.strip()]
    tat_ca = list(dict.fromkeys([settings.GEMINI_MODEL, *du_phong]))
    # Bỏ qua model vừa quá tải để mỗi lần gọi không mất ~15s thử lại vô ích; tất cả đều đang nghỉ thì vẫn thử hết
    con_dung = [m for m in tat_ca if _qua_tai_den.get(m, 0) <= time.monotonic()]
    return con_dung or tat_ca


def _doc_json(data: dict[str, Any]) -> Any:
    # model có "thinking" có thể trả thêm part suy nghĩ -> chỉ ghép các part text thường
    parts = data["candidates"][0]["content"]["parts"]
    text = "".join(p["text"] for p in parts if "text" in p and not p.get("thought"))
    return json.loads(text)


def generate_json(prompt: str, schema: dict[str, Any], *, temperature: float = 0.2, so_lan_thu: int = 3) -> Any:
    """Gọi Gemini, ép trả JSON đúng `schema` (OpenAPI subset: OBJECT/ARRAY/STRING/NUMBER...).

    Model chính quá tải (429/5xx) sau `so_lan_thu` lần -> chuyển sang model trong GEMINI_MODEL_DU_PHONG.
    """
    if not settings.GEMINI_API_KEY:
        raise ExternalServiceError("Chưa cấu hình GEMINI_API_KEY", "GEMINI_NOT_CONFIGURED")

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": temperature,
            "maxOutputTokens": settings.GEMINI_MAX_TOKEN_RA,
        },
    }
    loi_cuoi = ""
    for model in _cac_model():
        for lan in range(so_lan_thu):
            try:
                r = httpx.post(
                    _URL.format(model=model),
                    headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                    json=body,
                    timeout=settings.HTTP_TIMEOUT_GIAY * 4,
                )
            except httpx.TimeoutException:
                # đã chờ tới 2 phút: thử lại cùng model chỉ mất thêm thời gian -> sang model kế
                r, loi_cuoi = None, "timeout"
                break
            except httpx.HTTPError as e:
                r, loi_cuoi = None, f"lỗi mạng: {e}"
            if r is not None and r.status_code == 200:
                try:
                    return _doc_json(r.json())
                except (KeyError, IndexError, ValueError) as e:
                    # JSON hỏng/bị cắt ở maxOutputTokens (model lặp vô hạn): model khác có thể trả đúng
                    loi_cuoi = f"dữ liệu không hợp lệ: {e}"
                    break
            if r is not None:
                loi_cuoi = f"HTTP {r.status_code}: {r.text[:200]}"
                if r.status_code == 404:
                    break  # model bị ngừng / không có cho key này
                if r.status_code not in _MA_THU_LAI:
                    raise ExternalServiceError(f"Gemini ({model}) lỗi {loi_cuoi}")
            logger.warning("Gemini %s lần %s/%s thất bại: %s", model, lan + 1, so_lan_thu, loi_cuoi[:120])
            if lan < so_lan_thu - 1:
                # 429 (vượt RPM free tier) / 503 (quá tải) thường hết sau vài giây
                time.sleep(5 * 2**lan)
        _qua_tai_den[model] = time.monotonic() + _NGHI_MODEL_QUA_TAI_GIAY
        logger.warning("Gemini %s không dùng được (%s), tạm bỏ qua 10 phút và chuyển model dự phòng", model, loi_cuoi[:80])
    raise ExternalServiceError(f"Gemini không trả được kết quả ở mọi model: {loi_cuoi}")


def nhan_dien_anh(anh: bytes, mime: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Gửi ảnh + prompt, trả JSON. Thử lần lượt GEMINI_MODEL_SCAN, không chờ/thử lại cùng model:
    người dùng đang đợi nên lỗi hay timeout là chuyển ngay sang model kế."""
    if not settings.GEMINI_API_KEY:
        raise ExternalServiceError("Chưa cấu hình GEMINI_API_KEY", "GEMINI_NOT_CONFIGURED")

    parts = [{"inline_data": {"mime_type": mime, "data": base64.b64encode(anh).decode()}}, {"text": prompt}]
    loi_cuoi = ""
    for model in [m.strip() for m in settings.GEMINI_MODEL_SCAN.split(",") if m.strip()]:
        config: dict[str, Any] = {"temperature": 0.1}
        if not model.startswith("gemma"):
            # Gemma không nhận responseSchema -> chỉ dựa vào prompt rồi tự tách JSON
            config |= {"responseMimeType": "application/json", "responseSchema": schema}
        try:
            r = httpx.post(
                _URL.format(model=model),
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                json={"contents": [{"role": "user", "parts": parts}], "generationConfig": config},
                timeout=settings.SCAN_TIMEOUT_GIAY,
            )
        except httpx.HTTPError as e:
            loi_cuoi = f"{model}: lỗi mạng/timeout ({type(e).__name__})"
            logger.warning("Scan %s", loi_cuoi)
            continue
        if r.status_code != 200:
            loi_cuoi = f"{model}: HTTP {r.status_code} {r.text[:150]}"
            logger.warning("Scan %s", loi_cuoi)
            continue
        try:
            data = r.json()
            parts_kq = data["candidates"][0]["content"]["parts"]
            text = "".join(p["text"] for p in parts_kq if "text" in p and not p.get("thought"))
            khop = re.search(r"\{.*\}", text, re.S)
            if khop is None:
                raise ValueError("không có JSON")
            return json.loads(khop.group(0))
        except (KeyError, IndexError, ValueError) as e:
            loi_cuoi = f"{model}: dữ liệu không hợp lệ ({e})"
            logger.warning("Scan %s", loi_cuoi)
    raise ExternalServiceError(f"Không nhận diện được ảnh lúc này, thử lại sau: {loi_cuoi}", "SCAN_KHONG_KHA_DUNG")
