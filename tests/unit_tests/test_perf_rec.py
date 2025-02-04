from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from filelock import Timeout
from sqlalchemy import text

from pytest_sqlguard.perf_rec import MissingQueryReferenceData, ReferenceFile, record_queries


class TestRecordQueries:
    def test_no_queries(self, session):
        with record_queries(session) as ctx:
            pass
        assert len(ctx.recorder.queries) == 0

    def test_simple_query_without_simplification(self, session):
        with record_queries(session, simplify_queries=False) as ctx:
            session.execute(text("SELECT 1"))
        assert len(ctx.recorder.queries) == 1
        assert ctx.recorder.queries[0].statement == "SELECT 1"

    def test_simple_query_with_simplification(self, session):
        with record_queries(session) as ctx:
            session.execute(text("SELECT 1"))
        assert len(ctx.recorder.queries) == 1
        assert ctx.recorder.queries[0].statement == "SELECT #"


class TestSaveToFile:
    def test_create_new_file(self, session, tmpdir):
        path = tmpdir / "test_save_to_file.yaml"
        assert not path.exists()

        with record_queries(session, path=path, name="foo", simplify_queries=False):
            session.execute(text("SELECT 1"))

        with path.open() as yaml_file:
            data = yaml.safe_load(yaml_file)
        assert data == {"foo": {"queries": [{"statement": "SELECT 1"}]}}

    def test_add_new_key_to_empty_file(self, session, tmpdir):
        path = tmpdir / "test_save_to_file.yaml"
        with path.open(mode="w") as yaml_file:
            yaml_file.write("")

        with record_queries(session, path=path, name="foo", simplify_queries=False):
            session.execute(text("SELECT 1"))

        with path.open() as yaml_file:
            data = yaml.safe_load(yaml_file)
        assert data == {"foo": {"queries": [{"statement": "SELECT 1"}]}}

    def test_add_new_key_to_existing_file(self, session, tmpdir):
        path = tmpdir / "test_save_to_file.yaml"
        with path.open(mode="w") as yaml_file:
            yaml.dump({"bar": {"queries": [{"statement": "SELECT 2"}]}}, yaml_file)

        with record_queries(session, path=path, name="foo", simplify_queries=False):
            session.execute(text("SELECT 1"))

        with path.open() as yaml_file:
            data = yaml.safe_load(yaml_file)
        assert data.keys() == {"foo", "bar"}
        assert data["foo"] == {"queries": [{"statement": "SELECT 1"}]}
        assert data["bar"] == {"queries": [{"statement": "SELECT 2"}]}

    def test_overwrite_key_in_existing_file(self, session, tmpdir):
        path = tmpdir / "test_save_to_file.yaml"
        with path.open(mode="w") as yaml_file:
            yaml.dump({"foo": {"queries": [{"statement": "SELECT 2"}]}}, yaml_file)

        with record_queries(
            session,
            path=path,
            name="foo",
            simplify_queries=False,
            overwrite_reference_data=True,
        ):
            session.execute(text("SELECT 1"))

        with path.open() as yaml_file:
            data = yaml.safe_load(yaml_file)
        assert data.keys() == {"foo"}
        assert data["foo"] == {"queries": [{"statement": "SELECT 1"}]}


class TestCompareToReferenceFile:
    REFERENCE_DATA = {"foo": {"queries": [{"statement": "SELECT 1"}]}}

    def test_query_matches_reference(self, session, tmpdir):
        path = tmpdir / "test_query_matches_reference.yaml"
        with path.open(mode="w") as yaml_file:
            yaml.dump(self.REFERENCE_DATA, yaml_file)
        with record_queries(session, path=path, name="foo", simplify_queries=False):
            session.execute(text("SELECT 1"))

    def test_query_does_not_match_reference(self, session, tmpdir):
        path = tmpdir / "test_query_matches_reference.yaml"
        with path.open(mode="w") as yaml_file:
            yaml.dump(self.REFERENCE_DATA, yaml_file)
        with pytest.raises(AssertionError):
            with record_queries(session, path=path, name="foo"):
                session.execute(text("SELECT 1"))

    def test_ignore_reference_mismatch_when_overwriting_it(self, session, tmpdir):
        path = tmpdir / "test_query_matches_reference.yaml"
        with path.open(mode="w") as yaml_file:
            yaml.dump(self.REFERENCE_DATA, yaml_file)
        with record_queries(
            session,
            path=path,
            name="foo",
            overwrite_reference_data=True,
        ):
            session.execute(text("SELECT 1"))

    def test_overwrite_save_if_queries_dont_match(self, session, tmpdir):
        path = tmpdir / "test_query_matches_reference.yaml"
        with path.open(mode="w") as yaml_file:
            yaml.dump(self.REFERENCE_DATA, yaml_file)
        context_manager = record_queries(
            session,
            path=path,
            name="foo",
            simplify_queries=False,
            overwrite_reference_data=True,
        )
        m_save = Mock()
        with patch.object(context_manager.reference, "save_reference_to_disk", m_save):
            with context_manager:
                session.execute(text("SELECT 2"))
            assert m_save.called

    def test_overwrite_do_not_save_if_queries_match(self, session, tmpdir):
        path = tmpdir / "test_query_matches_reference.yaml"
        with path.open(mode="w") as yaml_file:
            yaml.dump(self.REFERENCE_DATA, yaml_file)
        context_manager = record_queries(
            session,
            path=path,
            name="foo",
            simplify_queries=False,
            overwrite_reference_data=True,
        )
        m_save = Mock()
        with patch.object(context_manager.reference, "save_reference_to_disk", m_save):
            with context_manager:
                session.execute(text("SELECT 1"))
            assert not m_save.called

    def test_default_is_to_ignore_missing_reference_data(self, session, tmpdir):
        path = tmpdir / "test_query_matches_reference.yaml"
        assert not path.exists()
        with record_queries(session, path=path, name="foo", simplify_queries=False):
            session.execute(text("SELECT 1"))

    def test_fail_on_missing_reference_data(self, session, tmpdir):
        path = tmpdir / "test_query_matches_reference.yaml"
        assert not path.exists()
        with pytest.raises(MissingQueryReferenceData) as exc_info:
            with record_queries(
                session,
                path=path,
                name="foo",
                simplify_queries=False,
                fail_on_missing_reference_data=True,
            ):
                session.execute(text("SELECT 1"))
        assert str(exc_info.value) == f"Missing query reference data 'foo' in '{path}'"


class TestLocking:
    def test_cannot_read_key_from_locked_file(self, tmpdir):
        path = Path(tmpdir) / "locked_file.queries.yaml"
        # Set the timeout to 1sec so the test suite is not too long to run
        rfile1 = ReferenceFile(path, lock_path=path.with_suffix(".lock"), lock_timeout=1)
        rfile2 = ReferenceFile(path, lock_path=path.with_suffix(".lock"), lock_timeout=1)
        with rfile1.lock.acquire():
            with pytest.raises(Timeout):
                rfile2.read_key("key")

    def test_cannot_update_key_in_locked_file(self, tmpdir):
        path = Path(tmpdir) / "locked_file.queries.yaml"
        # Set the timeout to 1sec so the test suite is not too long to run
        rfile1 = ReferenceFile(path, lock_path=path.with_suffix(".lock"), lock_timeout=1)
        rfile2 = ReferenceFile(path, lock_path=path.with_suffix(".lock"), lock_timeout=1)
        with rfile1.lock.acquire():
            with pytest.raises(Timeout):
                rfile2.update_key("key", "value")
