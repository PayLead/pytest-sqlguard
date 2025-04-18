from books_cli.model_base import DBModelBase, SQLABase
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship


class Author(SQLABase, DBModelBase):
    __tablename__ = "authors"

    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False, default=20)

    books: Mapped[list["Book"]] = relationship(back_populates="author")  # noqa
