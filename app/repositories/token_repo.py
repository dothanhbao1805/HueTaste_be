import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.token_dat_lai_mat_khau import TokenDatLaiMatKhau


def create(db: Session, user_id: uuid.UUID, hashed_token: str, expires_at: datetime) -> TokenDatLaiMatKhau:
    token = TokenDatLaiMatKhau(idNguoiDung=user_id, maToken=hashed_token, hetHanLuc=expires_at)
    db.add(token)
    db.flush()
    return token


def get_by_hash(db: Session, hashed_token: str) -> TokenDatLaiMatKhau | None:
    return db.scalar(select(TokenDatLaiMatKhau).where(TokenDatLaiMatKhau.maToken == hashed_token))


def invalidate_all_for_user(db: Session, user_id: uuid.UUID) -> None:
    db.execute(
        update(TokenDatLaiMatKhau)
        .where(TokenDatLaiMatKhau.idNguoiDung == user_id, TokenDatLaiMatKhau.daSuDung.is_(False))
        .values(daSuDung=True)
    )
