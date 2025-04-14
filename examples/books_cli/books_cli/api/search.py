from books_cli.db import DB
from books_cli.operations.search import list_books_by_author_name
from books_cli.schemas.book import BookSchema
from fastapi.routing import APIRouter

router = APIRouter()


@router.get("/by-author-name/{name}")
def api_list_books_by_author_name(name: str, session: DB) -> list[BookSchema]:
    return list_books_by_author_name(name, session)
