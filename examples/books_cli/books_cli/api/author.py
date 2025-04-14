from books_cli.db import DB
from books_cli.operations.author import create_author, list_authors
from books_cli.schemas.author import AuthorCreateSchema, AuthorSchema
from fastapi import APIRouter

router = APIRouter()


@router.post("")
def new_author(author_info: AuthorCreateSchema, session: DB) -> AuthorSchema:
    author = create_author(author_info.name, author_info.age, session)
    return author


@router.get("")
def list_all_authors(session: DB) -> list[AuthorSchema]:
    return list_authors(session)
