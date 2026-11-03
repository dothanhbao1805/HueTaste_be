from sqlalchemy.orm import Session

from app.models.goi_y import GoiY
from app.models.ngu_canh import NguCanh


def create_ngu_canh(db: Session, **fields) -> NguCanh:
    nc = NguCanh(**fields)
    db.add(nc)
    db.flush()
    return nc


def create_goi_y(db: Session, **fields) -> GoiY:
    gy = GoiY(**fields)
    db.add(gy)
    db.flush()
    return gy
