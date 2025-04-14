from books_cli.models.author import Author
from books_cli.schemas.author import AuthorSchema
from sqlalchemy.orm.session import Session


def create_author(name: str, age: int, session: Session) -> AuthorSchema:
    author = Author(name=name, age=age)
    session.add(author)
    session.flush()
    return author.to_schema(AuthorSchema)


def list_authors(session: Session) -> list[AuthorSchema]:
    authors = session.query(Author).all()
    return [a.to_schema(AuthorSchema) for a in authors]
