"""Gọi LLM qua Groq (gpt-oss, Qwen...) - API tương thích OpenAI, có gói free.

Groq chỉ có chế độ `json_object` (JSON gốc phải là object) nên schema được đưa vào prompt và
mảng kết quả được bọc trong {"ketQua": [...]}; giá trị ngoài enum do thu_thap_service lọc lại.
"""
import json
import logging
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_URL = "https://api.groq.com/openai/v1/chat/completions"
_MA_THU_LAI = {429, 500, 502, 503}
_KHOA_BOC = "ketQua"
# gpt-oss là model suy luận: token suy luận tính chung vào giới hạn output, để mặc định nó có thể
# nghĩ ~3000 token rồi bị cắt giữa JSON (finish_reason=length -> HTTP 400 json_validate_failed)
_MAX_TOKEN_RA = 8192


def _tham_so_suy_luan(model: str) -> dict[str, Any]:
    return {"reasoning_effort": "low"} if "gpt-oss" in model else {}


def _cac_model() -> list[str]:
    du_phong = [m.strip() for m in settings.GROQ_MODEL_DU_PHONG.split(",") if m.strip()]
    return list(dict.fromkeys([settings.GROQ_MODEL, *du_phong]))


def _prompt_he_thong(schema: dict[str, Any]) -> str:
    la_mang = schema.get("type") == "ARRAY"
    mo_ta = schema if not la_mang else {"type": "OBJECT", "properties": {_KHOA_BOC: schema}}
    return (
        "Bạn là bộ trích xuất dữ liệu. Chỉ trả về MỘT JSON object hợp lệ, không thêm chữ nào khác. "
        "JSON phải đúng schema sau (OpenAPI; trường có 'enum' chỉ được dùng đúng các giá trị liệt kê):\n"
        + json.dumps(mo_ta, ensure_ascii=False)
    )


def _doc_ket_qua(noi_dung: str, schema: dict[str, Any]) -> Any:
    data = json.loads(noi_dung)
    if schema.get("type") != "ARRAY":
        return data
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get(_KHOA_BOC), list):
            return data[_KHOA_BOC]
        # model đặt tên khoá khác: lấy mảng đầu tiên tìm thấy
        return next((v for v in data.values() if isinstance(v, list)), [])
    return []


def generate_json(prompt: str, schema: dict[str, Any], *, temperature: float = 0.2, so_lan_thu: int = 3) -> Any:
    if not settings.GROQ_API_KEY:
        raise ExternalServiceError("Chưa cấu hình GROQ_API_KEY", "GROQ_NOT_CONFIGURED")

    loi_cuoi = ""
    for model in _cac_model():
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": _prompt_he_thong(schema)},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
            "max_completion_tokens": _MAX_TOKEN_RA,
            **_tham_so_suy_luan(model),
        }
        for lan in range(so_lan_thu):
            try:
                r = httpx.post(
                    _URL,
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json=body,
                    timeout=settings.HTTP_TIMEOUT_GIAY * 4,
                )
            except httpx.HTTPError as e:
                r, loi_cuoi = None, f"lỗi mạng: {e}"
            if r is not None and r.status_code == 200:
                try:
                    return _doc_ket_qua(r.json()["choices"][0]["message"]["content"], schema)
                except (KeyError, IndexError, ValueError) as e:
                    loi_cuoi = f"JSON không hợp lệ: {e}"  # thỉnh thoảng model trả JSON hỏng -> thử lại
            elif r is not None:
                loi_cuoi = f"HTTP {r.status_code}: {r.text[:200]}"
                json_hong = r.status_code == 400 and "json_validate_failed" in r.text
                if not json_hong and r.status_code in (400, 404) and "model" in r.text:
                    break  # model bị ngừng/đổi tên -> sang model dự phòng luôn
                if not json_hong and r.status_code not in _MA_THU_LAI:  # JSON hỏng là ngẫu nhiên -> thử lại
                    raise ExternalServiceError(f"Groq ({model}) lỗi {loi_cuoi}")
            logger.warning("Groq %s lần %s/%s thất bại: %s", model, lan + 1, so_lan_thu, loi_cuoi[:120])
            if lan < so_lan_thu - 1:
                time.sleep(3 * 2**lan)
        logger.warning("Groq %s không dùng được, chuyển model dự phòng", model)
    raise ExternalServiceError(f"Groq không phản hồi: {loi_cuoi}")
