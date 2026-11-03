"""Lưu ảnh người dùng tải lên vào UPLOAD_DIR; DB chỉ giữ đường dẫn /uploads/... (avatar, scan món)."""
import uuid
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import AppException, NotFoundError

TIEN_TO_URL = "/uploads/"


def _dinh_dang(noi_dung: bytes) -> str | None:
    # nhận diện bằng magic bytes, không tin content_type/tên file client gửi
    if noi_dung.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if noi_dung.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if noi_dung[:4] == b"RIFF" and noi_dung[8:12] == b"WEBP":
        return "webp"
    return None


def luu_anh(noi_dung: bytes, thu_muc_con: str) -> str:
    """Trả đường dẫn tương đối dạng /uploads/<thu_muc_con>/<yyyy>/<mm>/<uuid>.<ext>."""
    if len(noi_dung) > settings.UPLOAD_MAX_MB * 1024 * 1024:
        raise AppException("FILE_TOO_LARGE", f"Ảnh tối đa {settings.UPLOAD_MAX_MB:g}MB", 413)
    duoi = _dinh_dang(noi_dung)
    if duoi is None:
        raise AppException("INVALID_IMAGE", "Chỉ nhận ảnh JPEG, PNG hoặc WEBP", 400)
    tuong_doi = f"{thu_muc_con}/{datetime.now():%Y/%m}/{uuid.uuid4().hex}.{duoi}"
    dich = Path(settings.UPLOAD_DIR) / tuong_doi
    dich.parent.mkdir(parents=True, exist_ok=True)
    dich.write_bytes(noi_dung)
    return TIEN_TO_URL + tuong_doi


def duong_dan_file(tuong_doi: str) -> Path:
    """File thật cho /uploads/<tuong_doi>; chặn ../ thoát ra ngoài UPLOAD_DIR."""
    goc = Path(settings.UPLOAD_DIR).resolve()
    file = (goc / tuong_doi).resolve()
    if not file.is_relative_to(goc) or not file.is_file():
        raise NotFoundError("Không tìm thấy ảnh", "FILE_NOT_FOUND")
    return file
