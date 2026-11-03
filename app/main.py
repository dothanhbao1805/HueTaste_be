from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.services import luu_tru_service

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/uploads/{duong_dan:path}", include_in_schema=False)
def anh_tai_len(duong_dan: str):
    # route thay cho StaticFiles để UPLOAD_DIR đọc lúc chạy (test đổi được thư mục)
    return FileResponse(luu_tru_service.duong_dan_file(duong_dan))
