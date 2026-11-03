from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Lỗi nghiệp vụ. Service ném lỗi này, handler đổi thành JSON {code, message}."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Không tìm thấy dữ liệu", code: str = "NOT_FOUND"):
        super().__init__(code, message, 404)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Chưa xác thực", code: str = "UNAUTHORIZED"):
        super().__init__(code, message, 401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Không có quyền truy cập", code: str = "FORBIDDEN"):
        super().__init__(code, message, 403)


class ConflictError(AppException):
    def __init__(self, message: str = "Dữ liệu đã tồn tại", code: str = "CONFLICT"):
        super().__init__(code, message, 409)


class ExternalServiceError(AppException):
    """Gemini/Wikipedia/Serper lỗi hoặc chưa cấu hình key."""

    def __init__(self, message: str, code: str = "EXTERNAL_SERVICE_ERROR"):
        super().__init__(code, message, 502)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def _app_exc(_: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(_: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"code": "VALIDATION_ERROR", "message": "Dữ liệu không hợp lệ", "errors": errors},
        )
