from pathlib import Path

import yaml
from sqlalchemy import text

CURRENT_PATH_DIR = Path(__file__).parent

# Only one test for this one because it does not really reflect the
# usage we do of SQLGuard, it's mainly here to ensure that the basic stuff
# is not broken.


def test_file_is_created_and_contains_ok_stuff(session, sqlguard):
    query_file = CURRENT_PATH_DIR / "test_file_is_created_and_contains_ok_stuff.queries.yaml"
    query_file.unlink(missing_ok=True)

    with sqlguard(session):
        session.execute(
            text("""
            CREATE TABLE test_1(i int, t text)
        """)
        )
        session.execute(text("""SELECT * from test_1"""))
        session.commit()

    with open(query_file, "r") as fd:
        obj = yaml.safe_load(fd)

    queries = obj["test_file_is_created_and_contains_ok_stuff"]["queries"]
    assert queries
    assert len(queries) == 2
    assert "CREATE TABLE test_1(i int, t text)" == queries[0]["statement"]
