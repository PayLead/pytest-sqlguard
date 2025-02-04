import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session

from pytest_sqlguard.sqlguard import sqlguard as og_sqlguard


def pytest_addoption(parser):
    group = parser.getgroup("sqlguard", "Options for SQLGuard")
    group.addoption(
        "--sqlguard-fail-missing",
        dest="sqlguard_fail_missing",
        default=False,
        action="store_true",
        help="SQLGuard: Fail if queries are missing in the stored reference file",
    )
    group.addoption(
        "--sqlguard-overwrite",
        dest="sqlguard_overwrite",
        default=False,
        action="store_true",
        help="SQLGuard: Overwrite the stored reference file",
    )


@pytest.fixture(scope="function")
def enable_sqlguard_fail_missing(request):
    request.config.option.sqlguard_fail_missing = True


@pytest.fixture(scope="function")
def disable_sqlguard_fail_missing(request):
    request.config.option.sqlguard_fail_missing = False


@pytest.fixture(scope="function")
def enable_sqlguard_overwrite(request):
    request.config.option.sqlguard_overwrite = True


@pytest.fixture(scope="function")
def disable_sqlguard_overwrite(request):
    request.config.option.sqlguard_overwrite = False


@pytest.fixture(scope="session", autouse=True)
def engine(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / "test_db.sqlite"
    engine = create_engine(
        f"sqlite:////{db_path.absolute()}",
        poolclass=StaticPool,
        logging_name="sqlguard-tests",
    )
    print(f"TMP Dir for DB: {db_path.absolute()}")

    return engine


@pytest.fixture(scope="function")
def session(engine):
    _connection = engine.connect()
    _session = Session(autocommit=False, autoflush=True, bind=_connection)
    yield _session


@pytest.fixture(scope="function")
def sqlguard(request, tmp_path_factory):
    fail_on_missing_reference_data = request.config.option.sqlguard_fail_missing
    overwrite_reference_data = request.config.option.sqlguard_overwrite
    yield og_sqlguard(
        request,
        tmp_path_factory,
        fail_on_missing_reference_data,
        overwrite_reference_data,
    )
