from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base cho mọi model. Alembic/tests import `app.models` để đăng ký bảng vào metadata."""
