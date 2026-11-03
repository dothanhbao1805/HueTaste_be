"""Worker chạy định kỳ pipeline thu thập dữ liệu (tiến trình riêng, không chạy chung uvicorn).

Chạy từ thư mục be/:  python -m scripts.worker [--chay-ngay]
Lịch lấy từ .env: LICH_MON_AN, LICH_DIA_DIEM (cú pháp cron 5 trường, giờ Việt Nam).
"""
import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.constants import LoaiThuThap
from app.services import thu_thap_service

TZ = "Asia/Ho_Chi_Minh"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chay-ngay", action="store_true", help="Chạy thu thập toàn bộ 1 lần khi khởi động")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    scheduler = BlockingScheduler(timezone=TZ)
    # max_instances=1 + coalesce: job chạy lâu không bị chồng; khoá GET_LOCK chặn thêm với admin/CLI
    scheduler.add_job(
        thu_thap_service.chay,
        CronTrigger.from_crontab(settings.LICH_MON_AN, timezone=TZ),
        args=[LoaiThuThap.MON_AN],
        id="thu_thap_mon_an",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=6 * 3600,  # máy ngủ đúng giờ hẹn thì vẫn chạy bù khi thức dậy (trong 6 giờ)
    )
    scheduler.add_job(
        thu_thap_service.chay,
        CronTrigger.from_crontab(settings.LICH_DIA_DIEM, timezone=TZ),
        args=[LoaiThuThap.DIA_DIEM],
        id="thu_thap_dia_diem",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=6 * 3600,  # máy ngủ đúng giờ hẹn thì vẫn chạy bù khi thức dậy (trong 6 giờ)
    )
    if args.chay_ngay:
        thu_thap_service.chay(LoaiThuThap.TAT_CA)
    logging.info("Worker chạy: món ăn '%s', địa điểm '%s'", settings.LICH_MON_AN, settings.LICH_DIA_DIEM)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Dừng worker")


if __name__ == "__main__":
    main()
