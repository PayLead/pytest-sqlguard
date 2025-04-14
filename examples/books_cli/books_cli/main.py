from books_cli.api import author_router, search_router
from fastapi import FastAPI

app = FastAPI(
    title="Books API",
    version="0.9.9",
)
app.include_router(author_router, prefix="/author")
app.include_router(search_router, prefix="/search")
