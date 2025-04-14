from decimal import Decimal

from books_cli.models import Author
from books_cli.operations.author import create_author
from books_cli.operations.books import create_book
from books_cli.operations.search import list_books_by_author_name


def test_create_author(session):
    author = create_author(name="First", age=90, session=session)
    assert session.query(Author).first().name == "First"


def test_search_author(session, sqlguard):
    author = create_author(name="Second", age=90, session=session)
    book = create_book(
        title="Some Title",
        price=Decimal("98"),
        author_id=author.id,
        session=session,
    )
    # With SQLite, we need to commit to the DB in order to be able to use sqlguard
    # If you are using another DBMS, you won't have this issue, but with SQLite the
    # DB is locked when we write and the lock is released only on commit.
    session.commit()
    with sqlguard(session):
        # If you check closely the function list_books_by_author_name
        # you'll see that there is a more optimized way of getting the books
        # written and commented inside the function.
        # If you were to use it, you'll need to update the guarded SQL of this
        # test that is in the file test_author.queries.yaml.
        # This can be done by running: pytest tests/test_author.py::test_search_author --sqlguard-overwrite
        assert list_books_by_author_name("Second", session=session)[0].id == book.id
