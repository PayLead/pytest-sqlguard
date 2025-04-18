from decimal import Decimal

import typer
from books_cli.db import get_session
from books_cli.operations.author import create_author
from books_cli.operations.books import create_book  # noqa

app = typer.Typer()


@app.command()
def create(init: bool | None = None):
    from books_cli.db import engine
    from books_cli.model_base import SQLABase

    SQLABase.metadata.create_all(bind=engine)
    if init:
        session = next(get_session())
        tolkien = create_author(name="Tolkien", age=99, session=session)
        rothfuss = create_author(name="Rothfuss", age=55, session=session)
        create_book(title="Lord of the Rings", price=Decimal("50.4"), author_id=tolkien.id, session=session)
        create_book(title="Bilbo Baggins", price=Decimal("23.2"), author_id=tolkien.id, session=session)
        create_book(title="The Name of the Wind", price=Decimal("19.99"), author_id=rothfuss.id, session=session)
        session.commit()


@app.command()
def drop():
    from books_cli.db import engine
    from books_cli.model_base import SQLABase

    SQLABase.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    app()
