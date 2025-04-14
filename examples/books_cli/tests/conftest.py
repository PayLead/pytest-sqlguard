import pytest
from books_cli.db import get_session
from books_cli.main import app
from books_cli.model_base import SQLABase
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def engine():
    engine = create_engine("sqlite:///books-test.db", echo=True)
    SQLABase.metadata.drop_all(bind=engine)
    SQLABase.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def session(engine):
    session = Session(bind=engine, autoflush=True)

    def override_get_session():
        return session

    app.dependency_overrides[get_session] = override_get_session
    yield session
    session.commit()
    del app.dependency_overrides[get_session]


def pytest_addoption(parser):
    sqlguard_group = parser.getgroup("sqlguard", "Options for SQLGuard")
    sqlguard_group.addoption(
        "--sqlguard-fail-missing",
        dest="sqlguard_fail_missing",
        default=False,
        action="store_true",
        help="SQLGuard: Fail if queries are missing in the stored reference file.",
    )
    sqlguard_group.addoption(
        "--sqlguard-overwrite",
        dest="sqlguard_overwrite",
        default=False,
        action="store_true",
        help="SQLGuard: Overwrite the stored reference file.",
    )


@pytest.fixture(scope="function")
def sqlguard(request, tmp_path_factory, session):
    # We use the previously defined pytest cli arguments
    fail_on_missing_reference_data = request.config.option.sqlguard_fail_missing
    overwrite_reference_data = request.config.option.sqlguard_overwrite

    from pytest_sqlguard.sqlguard import sqlguard as sqlguard_function

    yield sqlguard_function(
        request,
        tmp_path_factory,
        fail_on_missing_reference_data,
        overwrite_reference_data,
    )


@pytest.fixture(scope="function")
def test_client(session: Session):
    with TestClient(app) as test_client:
        yield test_client
