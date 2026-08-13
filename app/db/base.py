import uuid
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID  # noqa: N811
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeEngine


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[type, TypeEngine[Any]]] = {
        str: Text(),
        datetime: DateTime(timezone=True),
        uuid.UUID: PgUUID(as_uuid=True),
    }


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
