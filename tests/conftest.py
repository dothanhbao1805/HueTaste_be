import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  đăng ký bảng vào metadata
from app.core import security
from app.core.constants import VaiTro
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.nguoi_dung import NguoiDung


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as session:
        yield session
    engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db_session):
    user = NguoiDung(
        email="admin@test.com",
        matKhauMaHoa=security.hash_password("adminpass123"),
        hoTen="Admin",
        vaiTro=VaiTro.ADMIN.value,
        trangThai="active",
    )
    db_session.add(user)
    db_session.commit()
    return user


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user_token(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "user@test.com", "matKhau": "password123", "hoTen": "Nguyen Van A"},
    )
    assert r.status_code == 201
    return r.json()["accessToken"]
