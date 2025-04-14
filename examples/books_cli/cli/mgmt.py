import rich
import typer
from books_cli.db import get_session
from books_cli.operations.author import create_author, list_authors  # noqa

app = typer.Typer()


@app.command()
def create(name: str, age: int):
    session = next(get_session())
    author = create_author(name=name, age=age, session=session)
    session.commit()
    rich.print("Created author:", author)


@app.command()
def list():
    session = next(get_session())
    authors = list_authors(session)
    rich.print("Authors:", authors)


if __name__ == "__main__":
    app()
