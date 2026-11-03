import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Gửi email qua SMTP. Nếu chưa cấu hình SMTP_HOST thì chỉ log (dùng khi dev)."""
    if not settings.SMTP_HOST:
        logger.warning("[DEV EMAIL] to=%s subject=%s\n%s", to, subject, body)
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


def send_reset_password_email(to: str, raw_token: str) -> None:
    link = f"{settings.RESET_PASSWORD_URL}{raw_token}"
    send_email(
        to,
        "Đặt lại mật khẩu",
        f"Bạn vừa yêu cầu đặt lại mật khẩu.\nMở liên kết sau (hết hạn sau "
        f"{settings.RESET_TOKEN_EXPIRE_MINUTES} phút):\n{link}\n\n"
        f"Mã token: {raw_token}\nNếu không phải bạn, hãy bỏ qua email này.",
    )
