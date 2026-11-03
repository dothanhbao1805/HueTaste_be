"""Điểm gọi LLM duy nhất của pipeline: thử lần lượt các nhà cung cấp theo LLM_THU_TU."""
import logging
from collections.abc import Callable
from typing import Any

from app.core.config import settings
from app.core.exceptions import ExternalServiceError
from app.services import gemini_service, groq_service

logger = logging.getLogger(__name__)

_MA_CHUA_CO_KEY = {"GROQ_NOT_CONFIGURED", "GEMINI_NOT_CONFIGURED"}


def _nha_cung_cap(thu_tu: str | None = None) -> list[tuple[str, Callable[..., Any]]]:
    bang = {"groq": groq_service.generate_json, "gemini": gemini_service.generate_json}
    ten = [t.strip() for t in (thu_tu or settings.LLM_THU_TU).split(",") if t.strip() in bang]
    return [(t, bang[t]) for t in dict.fromkeys(ten)]


def generate_json(prompt: str, schema: dict[str, Any], *, temperature: float = 0.2, thu_tu: str | None = None) -> Any:
    """`thu_tu`: CSV nhà cung cấp cho riêng lời gọi này (vd "gemini,groq"), mặc định LLM_THU_TU."""
    loi: list[str] = []
    co_key = False
    for ten, goi in _nha_cung_cap(thu_tu):
        try:
            return goi(prompt, schema, temperature=temperature)
        except ExternalServiceError as e:
            if e.code not in _MA_CHUA_CO_KEY:
                co_key = True
                logger.warning("LLM %s lỗi, thử nhà cung cấp kế tiếp: %s", ten, e.message[:150])
            loi.append(f"{ten}: {e.message[:150]}")
    if not co_key:
        raise ExternalServiceError(
            "Chưa cấu hình LLM: cần GROQ_API_KEY hoặc GEMINI_API_KEY trong .env", "LLM_NOT_CONFIGURED"
        )
    raise ExternalServiceError("Mọi nhà cung cấp LLM đều lỗi - " + " | ".join(loi))
