from app.services import email_service
from tests.conftest import auth_header


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_login_me(client):
    body = {"email": "A@Test.com", "matKhau": "password123", "hoTen": "A"}
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 201
    assert r.json()["nguoiDung"]["email"] == "a@test.com"

    assert client.post("/api/v1/auth/register", json=body).status_code == 409

    r = client.post("/api/v1/auth/login", json={"email": "a@test.com", "matKhau": "password123"})
    assert r.status_code == 200
    token = r.json()["accessToken"]

    me = client.get("/api/v1/users/me", headers=auth_header(token))
    assert me.status_code == 200 and me.json()["hoTen"] == "A"


def test_login_wrong_password(client, user_token):
    r = client.post("/api/v1/auth/login", json={"email": "user@test.com", "matKhau": "wrongpass1"})
    assert r.status_code == 401
    assert r.json()["code"] == "INVALID_CREDENTIALS"


def test_me_requires_auth(client):
    assert client.get("/api/v1/users/me").status_code == 401


def test_refresh(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "r@test.com", "matKhau": "password123", "hoTen": "R"},
    )
    refresh = r.json()["refreshToken"]
    assert client.post("/api/v1/auth/refresh", json={"refreshToken": refresh}).status_code == 200
    # access token không dùng được làm refresh
    access = r.json()["accessToken"]
    assert client.post("/api/v1/auth/refresh", json={"refreshToken": access}).status_code == 401


def test_update_profile_and_change_password(client, user_token):
    h = auth_header(user_token)
    r = client.patch("/api/v1/users/me", json={"hoTen": "Ten Moi"}, headers=h)
    assert r.status_code == 200 and r.json()["hoTen"] == "Ten Moi"

    bad = client.post(
        "/api/v1/users/me/change-password",
        json={"matKhauCu": "sai", "matKhauMoi": "newpassword1"},
        headers=h,
    )
    assert bad.status_code == 400
    ok = client.post(
        "/api/v1/users/me/change-password",
        json={"matKhauCu": "password123", "matKhauMoi": "newpassword1"},
        headers=h,
    )
    assert ok.status_code == 200
    r = client.post("/api/v1/auth/login", json={"email": "user@test.com", "matKhau": "newpassword1"})
    assert r.status_code == 200


def test_forgot_and_reset_password(client, user_token, monkeypatch):
    sent = {}
    monkeypatch.setattr(
        email_service, "send_reset_password_email", lambda to, raw: sent.update(to=to, token=raw)
    )
    r = client.post("/api/v1/auth/forgot-password", json={"email": "user@test.com"})
    assert r.status_code == 200 and sent["to"] == "user@test.com"

    # email không tồn tại vẫn trả 200, không gửi mail
    sent.clear()
    assert client.post("/api/v1/auth/forgot-password", json={"email": "no@test.com"}).status_code == 200
    assert not sent

    r = client.post("/api/v1/auth/forgot-password", json={"email": "user@test.com"})
    token = sent["token"]
    r = client.post(
        "/api/v1/auth/reset-password", json={"token": token, "matKhauMoi": "resetpass123"}
    )
    assert r.status_code == 200
    # token chỉ dùng được một lần
    r = client.post(
        "/api/v1/auth/reset-password", json={"token": token, "matKhauMoi": "another12345"}
    )
    assert r.status_code == 400 and r.json()["code"] == "INVALID_RESET_TOKEN"
    r = client.post("/api/v1/auth/login", json={"email": "user@test.com", "matKhau": "resetpass123"})
    assert r.status_code == 200
