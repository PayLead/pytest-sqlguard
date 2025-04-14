from decimal import Decimal
from uuid import UUID

from books_cli.models import Book
from books_cli.schemas.book import BookSchema
from sqlalchemy.orm.session import Session


def create_book(title: str, price: Decimal, author_id: UUID, session: Session) -> BookSchema:
    book = Book(title=title, price=price, author_id=author_id)
    session.add(book)
    session.flush()
    return book.to_schema(BookSchema)
