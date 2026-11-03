import uuid

from sqlalchemy import CHAR
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UUIDChar36(TypeDecorator[uuid.UUID]):
    """UUID lưu dạng CHAR(36) có gạch nối, khớp với `DEFAULT (uuid())` của MySQL.

    `sqlalchemy.Uuid` trên MySQL lưu CHAR(32) không gạch nối nên không so khớp được
    với bản ghi do MySQL tự sinh.
    """

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value: uuid.UUID | str | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return str(value if isinstance(value, uuid.UUID) else uuid.UUID(str(value)))

    def process_result_value(self, value: str | None, dialect: Dialect) -> uuid.UUID | None:
        return None if value is None else uuid.UUID(value)
