from decimal import Decimal

from books_cli.operations.author import create_author
from books_cli.operations.books import create_book


def test_author_search_api(session, sqlguard, test_client):
    author = create_author(name="API Author", age=90, session=session)
    book = create_book(
        title="API Title",
        price=Decimal("98"),
        author_id=author.id,
        session=session,
    )
    session.commit()
    with sqlguard(session):
        # If you check closely the API route (defined in the function api_list_books_by_author_name)
        # you'll see that it calls list_books_by_author_name and that
        # there  is a more optimized way of getting the books
        # written and commented inside that function.
        # If you were to use it, you'll need to update the guarded SQL of this
        # test that is in the file test_author_api.queries.yaml.
        # This can be done by running: pytest tests/test_author.py::test_search_author_api --sqlguard-overwrite
        res = test_client.get("/search/by-author-name/API Author")

    assert res.status_code == 200
    assert res.json()[0]["id"] == str(book.id)
