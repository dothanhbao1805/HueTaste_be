import re
import unicodedata
from difflib import SequenceMatcher


def chuan_hoa_ten(ten: str) -> str:
    """Khoá so trùng: "Bún Bò  Huế!" -> "bun bo hue". `đ` không tách dấu được bằng NFD nên đổi tay."""
    s = ten.replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return s.strip()


def do_tuong_dong(a: str, b: str) -> float:
    return SequenceMatcher(None, chuan_hoa_ten(a), chuan_hoa_ten(b)).ratio()
