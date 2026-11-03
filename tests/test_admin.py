from tests.conftest import auth_header


def _admin_token(client):
    r = client.post(
        "/api/v1/auth/admin/login", json={"email": "admin@test.com", "matKhau": "adminpass123"}
    )
    assert r.status_code == 200
    return r.json()["accessToken"]


def test_user_cannot_use_admin_login(client, user_token):
    r = client.post(
        "/api/v1/auth/admin/login", json={"email": "user@test.com", "matKhau": "password123"}
    )
    assert r.status_code == 403 and r.json()["code"] == "NOT_ADMIN"


def test_user_forbidden_on_admin_endpoints(client, user_token):
    r = client.get("/api/v1/admin/users", headers=auth_header(user_token))
    assert r.status_code == 403


def test_admin_list_search_and_block(client, admin_user, user_token):
    h = auth_header(_admin_token(client))

    r = client.get("/api/v1/admin/users", headers=h)
    assert r.status_code == 200 and r.json()["total"] == 2

    r = client.get("/api/v1/admin/users", params={"q": "user@", "vaiTro": "user"}, headers=h)
    assert r.json()["total"] == 1
    uid = r.json()["items"][0]["idNguoiDung"]

    r = client.patch(f"/api/v1/admin/users/{uid}/status", json={"trangThai": "blocked"}, headers=h)
    assert r.status_code == 200 and r.json()["trangThai"] == "blocked"

    # user bị khóa không đăng nhập / dùng token cũ được
    r = client.post("/api/v1/auth/login", json={"email": "user@test.com", "matKhau": "password123"})
    assert r.status_code == 403
    assert client.get("/api/v1/users/me", headers=auth_header(user_token)).status_code == 403


def test_admin_cannot_block_self(client, admin_user):
    h = auth_header(_admin_token(client))
    r = client.patch(
        f"/api/v1/admin/users/{admin_user.idNguoiDung}/status", json={"trangThai": "blocked"}, headers=h
    )
    assert r.status_code == 400 and r.json()["code"] == "CANNOT_CHANGE_SELF"
