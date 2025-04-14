from contextlib import contextmanager
from decimal import Decimal

import rich
import typer
from books_cli.model_base import SQLABase
from books_cli.operations.author import create_author, list_authors
from books_cli.operations.books import create_book
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

app = typer.Typer(no_args_is_help=True)

engine = create_engine("sqlite:///books.db", echo=True)


@contextmanager
def session() -> Session:
    with Session(autoflush=True, bind=engine) as session:
        yield session
        session.commit()


@app.command()
def init_db():
    SQLABase.metadata.create_all(bind=engine)
    with session() as _session:
        tolkien = create_author(name="Tolkien", age=99, session=_session)
        rothfuss = create_author(name="Rothfuss", age=55, session=_session)
        create_book(title="Lord of the Rings", price=Decimal("50.4"), author_id=tolkien.id, session=_session)
        create_book(title="Bilbo Baggins", price=Decimal("23.2"), author_id=tolkien.id, session=_session)
        create_book(title="The Name of the Wind", price=Decimal("19.99"), author_id=rothfuss.id, session=_session)


@app.command()
def drop_db():
    SQLABase.metadata.drop_all(bind=engine)


authors = typer.Typer()
app.add_typer(authors, name="authors")


@authors.command(name="create")
def create_auth(name: str, age: int):
    with session() as _session:
        author = create_author(name=name, age=age, session=_session)
    rich.print("Created author:", author)


@authors.command(name="list")
def list_auth():
    with session() as _session:
        authors = list_authors(_session)
    rich.print("Authors:", authors)


if __name__ == "__main__":
    app()
