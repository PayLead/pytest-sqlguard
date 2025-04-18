from books_cli.models.author import Author
from books_cli.schemas.book import BookSchema
from sqlalchemy.orm import Session


def list_books_by_author_name(author_name: str, session: Session) -> list[BookSchema]:
    author = session.query(Author).where(Author.name == author_name).first()
    if author:
        books = author.books
        return [b.to_schema(BookSchema) for b in books]

    # Instead of doing two queries like the above,
    # the same result can be obtained by doing:
    # ==== Uncomment =====
    # from books_cli.models.book import Book

    # books = session.query(Book).join(Author, Author.id == Book.author_id).where(Author.name == author_name).all()
    # return [b.to_schema(BookSchema) for b in books]
    # === Enf of Uncomment ==
    # However if you do that, you need to update the guarded SQL present in
    # test_author.queries.yaml["test_search_author"]
    # You can do this with the command: pytest tests/test_author.py::test_search_author --sqlguard-overwrite
    return []
