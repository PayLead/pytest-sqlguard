from decimal import Decimal

from books_cli.model_base import DBModelBase, SQLABase
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy_utils.types.uuid import UUIDType


class Book(SQLABase, DBModelBase):
    __tablename__ = "books"

    title = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False, default=Decimal("20.0"))
    author_id = Column(UUIDType, ForeignKey("authors.id"), nullable=False)

    author: Mapped["Author"] = relationship(back_populates="books")  # noqa
