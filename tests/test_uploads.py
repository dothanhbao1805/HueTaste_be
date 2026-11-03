import pytest

from app.core.config import settings
from tests.conftest import auth_header

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.fixture(autouse=True)
def thu_muc_tam(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


def test_upload_anh_va_tai_lai(client, user_token, thu_muc_tam):
    r = client.post(
        "/api/v1/uploads", params={"loai": "mon_an"}, files={"file": ("a.png", PNG, "image/png")},
        headers=auth_header(user_token),
    )
    assert r.status_code == 201, r.text
    url = r.json()["url"]
    assert url.startswith("http://testserver/uploads/mon_an/") and url.endswith(".png")
    assert len(list(thu_muc_tam.rglob("*.png"))) == 1
    tai = client.get(url.removeprefix("http://testserver"))
    assert tai.status_code == 200 and tai.content == PNG


def test_upload_tu_choi_file_khong_phai_anh_va_qua_co(client, user_token, monkeypatch):
    h = auth_header(user_token)
    # content_type nói là ảnh nhưng nội dung là text -> vẫn bị chặn
    r = client.post("/api/v1/uploads", files={"file": ("a.jpg", b"hello", "image/jpeg")}, headers=h)
    assert r.status_code == 400 and r.json()["code"] == "INVALID_IMAGE"
    monkeypatch.setattr(settings, "UPLOAD_MAX_MB", 0.00001)  # ~10 byte
    r = client.post("/api/v1/uploads", files={"file": ("a.png", PNG, "image/png")}, headers=h)
    assert r.status_code == 413 and r.json()["code"] == "FILE_TOO_LARGE"
    assert client.post("/api/v1/uploads", files={"file": ("a.png", PNG, "image/png")}).status_code == 401


def test_upload_avatar_cap_nhat_ho_so(client, user_token):
    h = auth_header(user_token)
    r = client.post("/api/v1/users/me/avatar", files={"file": ("me.jpg", JPG, "image/jpeg")}, headers=h)
    assert r.status_code == 200 and "/uploads/avatar/" in r.json()["anhDaiDien"]
    assert client.get("/api/v1/users/me", headers=h).json()["anhDaiDien"] == r.json()["anhDaiDien"]


def test_khong_doc_file_ngoai_thu_muc_upload(client):
    assert client.get("/uploads/..%2F..%2Fpytest.ini").status_code == 404
    assert client.get("/uploads/khong-co.png").status_code == 404
