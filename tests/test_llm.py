"""Groq/Gemini/llm_service với httpx giả: không gọi mạng thật, không chờ sleep."""
import json

import httpx
import pytest

from app.core.config import settings
from app.core.exceptions import ExternalServiceError
from app.services import gemini_service, groq_service, llm_service

SCHEMA_MANG = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"tenMon": {"type": "STRING"}}}}


class _Resp:
    def __init__(self, status: int, data: dict | None = None, text: str = ""):
        self.status_code, self._data, self.text = status, data or {}, text or json.dumps(data or {})

    def json(self):
        return self._data


def _groq_ok(noi_dung: dict) -> _Resp:
    return _Resp(200, {"choices": [{"message": {"content": json.dumps(noi_dung, ensure_ascii=False)}}]})


def _gemini_ok(noi_dung) -> _Resp:
    text = json.dumps(noi_dung, ensure_ascii=False)
    return _Resp(200, {"candidates": [{"content": {"parts": [{"text": "suy nghĩ", "thought": True}, {"text": text}]}}]})


@pytest.fixture(autouse=True)
def khong_ngu(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "k-groq")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "k-gemini")
    monkeypatch.setattr(settings, "GROQ_MODEL", "llama-a")
    monkeypatch.setattr(settings, "GROQ_MODEL_DU_PHONG", "llama-b")
    gemini_service._qua_tai_den.clear()


def _gia_lap_post(monkeypatch, phan_hoi: list[_Resp]) -> list[dict]:
    goi: list[dict] = []

    def fake_post(url, headers=None, json=None, timeout=None):
        goi.append({"url": url, "body": json})
        kq = phan_hoi.pop(0)
        if isinstance(kq, Exception):
            raise kq
        return kq

    monkeypatch.setattr("httpx.post", fake_post)
    return goi


def test_groq_mo_boc_mang_va_dua_schema_vao_prompt(monkeypatch):
    goi = _gia_lap_post(monkeypatch, [_groq_ok({"ketQua": [{"tenMon": "Bún bò Huế"}]})])
    assert groq_service.generate_json("liệt kê", SCHEMA_MANG) == [{"tenMon": "Bún bò Huế"}]
    body = goi[0]["body"]
    assert body["model"] == "llama-a" and body["response_format"] == {"type": "json_object"}
    assert "ketQua" in body["messages"][0]["content"]  # schema mảng được bọc vào object


def test_groq_khoa_khac_ten_va_json_hong(monkeypatch):
    _gia_lap_post(monkeypatch, [_Resp(200, {"choices": [{"message": {"content": "{hỏng"}}]}), _groq_ok({"mon": [{"tenMon": "Chè"}]})])
    assert groq_service.generate_json("x", SCHEMA_MANG) == [{"tenMon": "Chè"}]


def test_groq_model_bi_ngung_chuyen_du_phong(monkeypatch):
    goi = _gia_lap_post(
        monkeypatch,
        [_Resp(404, text='{"error":{"message":"The model `llama-a` has been decommissioned"}}'), _groq_ok({"ketQua": []})],
    )
    assert groq_service.generate_json("x", SCHEMA_MANG) == []
    assert [g["body"]["model"] for g in goi] == ["llama-a", "llama-b"]


def test_groq_json_validate_failed_thi_thu_lai_va_gpt_oss_suy_luan_thap(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")
    loi = '{"error":{"message":"Failed to validate JSON.","code":"json_validate_failed","failed_generation":"model"}}'
    goi = _gia_lap_post(monkeypatch, [_Resp(400, text=loi), _groq_ok({"ketQua": [{"tenMon": "Chè"}]})])
    assert groq_service.generate_json("x", SCHEMA_MANG) == [{"tenMon": "Chè"}]
    assert [g["body"]["model"] for g in goi] == ["openai/gpt-oss-120b"] * 2  # thử lại cùng model
    assert goi[0]["body"]["reasoning_effort"] == "low" and goi[0]["body"]["max_completion_tokens"] == 8192
    assert "reasoning_effort" not in groq_service._tham_so_suy_luan("llama-b")


def test_llm_service_groq_loi_thi_dung_gemini(monkeypatch):
    monkeypatch.setattr(settings, "LLM_THU_TU", "groq,gemini")
    # Groq: 2 model x 3 lần đều 503 -> chuyển Gemini
    goi = _gia_lap_post(monkeypatch, [_Resp(503)] * 6 + [_gemini_ok([{"tenMon": "Bánh bèo"}])])
    assert llm_service.generate_json("x", SCHEMA_MANG) == [{"tenMon": "Bánh bèo"}]
    assert "groq.com" in goi[0]["url"] and "generativelanguage" in goi[-1]["url"]


def test_llm_service_bo_qua_nha_cung_cap_chua_co_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    goi = _gia_lap_post(monkeypatch, [_gemini_ok({"a": 1})])
    assert llm_service.generate_json("x", {"type": "OBJECT"}) == {"a": 1}
    assert len(goi) == 1

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    with pytest.raises(ExternalServiceError) as e:
        llm_service.generate_json("x", {"type": "OBJECT"})
    assert e.value.code == "LLM_NOT_CONFIGURED"


def test_gemini_model_qua_tai_bi_bo_qua_lan_sau(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_MODEL", "flash")
    monkeypatch.setattr(settings, "GEMINI_MODEL_DU_PHONG", "lite")
    goi = _gia_lap_post(monkeypatch, [_Resp(503)] * 3 + [_gemini_ok({"a": 1}), _gemini_ok({"a": 2})])
    assert gemini_service.generate_json("x", {"type": "OBJECT"}) == {"a": 1}
    assert gemini_service.generate_json("y", {"type": "OBJECT"}) == {"a": 2}
    models = [g["url"].split("/models/")[1].split(":")[0] for g in goi]
    assert models == ["flash", "flash", "flash", "lite", "lite"]  # lần 2 không thử lại 'flash' đang nghỉ


def _models(goi):
    return [g["url"].split("/models/")[1].split(":")[0] for g in goi]


def test_llm_service_thu_tu_theo_tung_loi_goi(monkeypatch):
    monkeypatch.setattr(settings, "LLM_THU_TU", "groq,gemini")
    goi = _gia_lap_post(monkeypatch, [_gemini_ok({"a": 1})])
    assert llm_service.generate_json("x", {"type": "OBJECT"}, thu_tu="gemini,groq") == {"a": 1}
    assert "generativelanguage" in goi[0]["url"]  # Gemini được gọi trước dù LLM_THU_TU mặc định là groq
    assert goi[0]["body"]["generationConfig"]["maxOutputTokens"] == settings.GEMINI_MAX_TOKEN_RA


def test_gemini_timeout_hoac_json_hong_chuyen_ngay_model_ke(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_MODEL", "flash")
    monkeypatch.setattr(settings, "GEMINI_MODEL_DU_PHONG", "lite,cuoi")
    hong = _Resp(200, {"candidates": [{"content": {"parts": [{"text": '{"a": [1, 1, 1, 1'}]}}]})
    goi = _gia_lap_post(monkeypatch, [httpx.ReadTimeout("chậm"), hong, _gemini_ok({"a": 3})])
    assert gemini_service.generate_json("x", {"type": "OBJECT"}) == {"a": 3}
    assert _models(goi) == ["flash", "lite", "cuoi"]  # không thử lại cùng model


def test_gemini_model_bi_ngung_404_chuyen_model_ke(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_MODEL", "cu")
    monkeypatch.setattr(settings, "GEMINI_MODEL_DU_PHONG", "moi")
    goi = _gia_lap_post(monkeypatch, [_Resp(404, {"error": "no longer available"}), _gemini_ok({"a": 1})])
    assert gemini_service.generate_json("x", {"type": "OBJECT"}) == {"a": 1}
    assert _models(goi) == ["cu", "moi"]


def test_gemini_het_model_thi_bao_loi_de_llm_service_chuyen_groq(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_MODEL", "flash")
    monkeypatch.setattr(settings, "GEMINI_MODEL_DU_PHONG", "")
    goi = _gia_lap_post(monkeypatch, [httpx.ReadTimeout("chậm"), _groq_ok({"a": 9})])
    assert llm_service.generate_json("x", {"type": "OBJECT"}, thu_tu="gemini,groq") == {"a": 9}
    assert "groq" in goi[1]["url"]
