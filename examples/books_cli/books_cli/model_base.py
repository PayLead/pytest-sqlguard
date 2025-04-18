from datetime import datetime, timezone
from typing import Type

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_base
from sqlalchemy_utils import UUIDType
from ulid import ULID

Base = declarative_base()


class SQLABase(Base):
    __abstract__ = True

    def to_schema(self, schema: Type[BaseModel]):
        return schema.model_validate(self, from_attributes=True)


class DBModelBase:
    id = Column(
        UUIDType,
        primary_key=True,
        default=lambda: ULID().to_uuid(),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
