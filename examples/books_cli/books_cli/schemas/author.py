from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuthorCreateSchema(BaseModel):
    name: str
    age: int = 20


class AuthorSchema(BaseModel):
    id: UUID
    created_at: datetime
    name: str
    age: int
