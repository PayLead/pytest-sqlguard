from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic.main import BaseModel


class BookSchema(BaseModel):
    id: UUID
    created_at: datetime
    title: str
    price: Decimal
    author_id: UUID
