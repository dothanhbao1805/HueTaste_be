"""Chạy pipeline thu thập 1 lần.

Chạy từ thư mục be/:
  python -m scripts.thu_thap_du_lieu --mon-an --so-mon 20
  python -m scripts.thu_thap_du_lieu --dia-diem
"""
import argparse
import json
import logging

from app.core.constants import LoaiThuThap
from app.services import thu_thap_service


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mon-an", action="store_true", help="Gemini + Wikipedia -> MonAn")
    parser.add_argument("--dia-diem", action="store_true", help="Serper (Google Maps) -> DiaDiem")
    parser.add_argument("--so-mon", type=int, default=None, help="Số món tối đa (mặc định THU_THAP_SO_MON)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.mon_an and args.dia_diem or not (args.mon_an or args.dia_diem):
        loai = LoaiThuThap.TAT_CA
    else:
        loai = LoaiThuThap.MON_AN if args.mon_an else LoaiThuThap.DIA_DIEM

    ket_qua = thu_thap_service.chay(loai, args.so_mon)
    if ket_qua is None:
        print("Đang có tiến trình thu thập khác chạy, thử lại sau.")
    else:
        print(json.dumps(ket_qua, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
