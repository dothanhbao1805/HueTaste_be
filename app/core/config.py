from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Hue Food Recommender API"
    DEBUG: bool = False

    DATABASE_URL: str = "mysql+pymysql://root:matkhau@localhost:3306/hue_food?charset=utf8mb4"

    SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    RESET_PASSWORD_URL: str = "http://localhost:3000/reset-password?token="

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@hue-food.local"

    # Dịch vụ ngoài cho pipeline thu thập dữ liệu và gợi ý
    # LLM: thử lần lượt theo LLM_THU_TU, nhà cung cấp chưa có key thì bỏ qua
    LLM_THU_TU: str = "groq,gemini"
    # Theo benchmark: Groq gpt-oss liệt kê món hay lặp lại món đã có, Gemini trích tag dài hay lặp vô hạn
    LLM_THU_TU_DANH_SACH: str = "gemini,groq"  # bước liệt kê món mới
    LLM_THU_TU_TAG: str = "groq,gemini"  # bước trích tag/nguyên liệu theo lô
    GROQ_API_KEY: str = ""
    # Tên model theo danh sách GET https://api.groq.com/openai/v1/models của key (Groq hay đổi model)
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_MODEL_DU_PHONG: str = "qwen/qwen3.8-27b,openai/gpt-oss-20b"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    # Thử lần lượt khi model chính quá tải (503) hoặc hết quota phút (429), cách nhau dấu phẩy
    # gemini-flash-latest để cuối: trên gói free có lúc mất >80s cho 1 câu ngắn
    GEMINI_MODEL_DU_PHONG: str = "gemini-3.5-flash-lite,gemini-flash-latest"
    GEMINI_MAX_TOKEN_RA: int = 8192  # chặn model lặp vô hạn khi trả JSON dài
    # Scan ảnh món: thử lần lượt, lỗi/timeout chuyển ngay model kế (benchmark: Flash-Lite nhanh và đúng nhất)
    GEMINI_MODEL_SCAN: str = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemma-4-26b-a4b-it"
    SCAN_TIMEOUT_GIAY: float = 20.0
    SCAN_TOI_DA_MOI_NGAY: int = 30  # mỗi người dùng, chống đốt quota free và spam tạo món
    SCAN_CHO_LAM_GIAU_GIAY: int = 120  # quá thời gian này mà món vẫn unverified -> CHUA_XAC_MINH
    SERPER_API_KEY: str = ""  # serper.dev - tìm quán trên Google Maps
    WIKI_USER_AGENT: str = "HueTasteBot/0.1 (do-an-tot-nghiep; contact: admin@hue-food.local)"
    HTTP_TIMEOUT_GIAY: float = 30.0

    # Tâm TP Huế (gần Cầu Tràng Tiền) và bán kính lấy quán
    HUE_VI_DO: float = 16.4637
    HUE_KINH_DO: float = 107.5909
    HUE_BAN_KINH_KM: float = 20.0

    # Worker: số món mỗi lần thu thập và lịch cron (phút giờ ngày tháng thứ)
    THU_THAP_SO_MON: int = 120
    THU_THAP_QUAN_MOI_MON: int = 8
    # Ảnh phụ của món/quán qua Serper Images (mỗi món/quán 1 lượt Serper, chỉ khi chưa có ảnh)
    THU_THAP_ANH_BAT: bool = True
    THU_THAP_SO_ANH_MON: int = 6
    THU_THAP_SO_ANH_QUAN: int = 5
    THU_THAP_ANH_RONG_TOI_THIEU: int = 400
    LICH_MON_AN: str = "0 3 1 * *"
    LICH_DIA_DIEM: str = "0 3 * * 1"

    # Ảnh người dùng tải lên (avatar, ảnh scan món) lưu trên đĩa, phục vụ ở /uploads/...
    UPLOAD_DIR: str = "uploads"
    UPLOAD_MAX_MB: float = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
