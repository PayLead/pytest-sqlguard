from pathlib import Path

import pytest
import yaml
from sqlalchemy import text

from pytest_sqlguard.perf_rec import MissingQueryReferenceData

CURRENT_PATH_FILE = Path(__file__)
CURRENT_PATH_DIR = CURRENT_PATH_FILE.parent
CURRENT_QUERY_FILE = CURRENT_PATH_FILE.with_suffix(".queries.yaml")


class TestSQLGuardFailMissing:
    @pytest.mark.usefixtures("enable_sqlguard_fail_missing")
    def test_enabled(self, session, sqlguard):
        # Don't commit in git the queries added by this test otherwise you'll
        # see it fail with "It does not raise MissingQueryReferenceData"
        with pytest.raises(MissingQueryReferenceData):
            with sqlguard(session):
                session.execute(
                    text("""
                    CREATE TABLE TestSQLGuardFailMissing_test_enabled(i int, t text)
                """)
                )
                session.commit()

        # The query file is still generated, remove the queries related to this
        # test in it so that they're not committed by mistake
        with open(CURRENT_QUERY_FILE, "r") as fd:
            obj = yaml.safe_load(fd)

        del obj["TestSQLGuardFailMissing::test_enabled"]
        with open(CURRENT_QUERY_FILE, "w") as fd:
            yaml.safe_dump(obj, fd)

    @pytest.mark.usefixtures("disable_sqlguard_fail_missing")
    def test_disabled(self, session, sqlguard):
        # We delete the recorded query for the test before checking it.
        # This should ensure that when the setting sqlguard_fail_missing is False
        # it does not raise when there is a missing query
        with open(CURRENT_QUERY_FILE, "r") as fd:
            obj = yaml.safe_load(fd)

        del obj["TestSQLGuardFailMissing::test_disabled"]
        with open(CURRENT_QUERY_FILE, "w") as fd:
            yaml.safe_dump(obj, fd)

        with sqlguard(session):
            session.execute(
                text("""
                CREATE TABLE TestSQLGuardFailMissing_test_disabled(i int, t text)
            """)
            )
            session.commit()


class TestSQLGuardOverwrite:
    @pytest.mark.usefixtures("enable_sqlguard_overwrite")
    def test_enabled(self, session, sqlguard):
        # Don't commit in git the queries added by this test otherwise you'll
        # see it fail with "It does not raise MissingQueryReferenceData"
        with sqlguard(session):
            session.execute(
                text("""
                CREATE TABLE TestSQLGuardOverwrite_test_enabled(i int, t text)
            """)
            )
            session.execute(text("SELECT * FROM TestSQLGuardOverwrite_test_enabled"))
            session.commit()

        # Remove the second query after the test has run. this will make it work
        # for the next run.
        with open(CURRENT_QUERY_FILE, "r") as fd:
            obj = yaml.safe_load(fd)
        oneline_loaded_second_query = " ".join(
            obj["TestSQLGuardOverwrite::test_enabled"]["queries"][1]["statement"].splitlines()
        )
        assert oneline_loaded_second_query == "SELECT * FROM TestSQLGuardOverwrite_test_enabled"
        del obj["TestSQLGuardOverwrite::test_enabled"]["queries"][1]
        with open(CURRENT_QUERY_FILE, "w") as fd:
            yaml.safe_dump(obj, fd)

    @pytest.mark.usefixtures("disable_sqlguard_overwrite")
    def test_disabled(self, session, sqlguard):
        with pytest.raises(AssertionError):
            with sqlguard(session):
                session.execute(
                    text("""
                    CREATE TABLE TestSQLGuardOverwrite_test_disabled(i int, t text)
                """)
                )
                session.execute(text("SELECT * FROM TestSQLGuardOverwrite_test_disabled"))
                session.commit()
