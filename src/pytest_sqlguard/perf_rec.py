from collections import Counter
from pathlib import Path
from typing import NamedTuple

import sqlalchemy.event
import yaml
from filelock import FileLock
from sqlalchemy import text
from sqlparse import format as sql_format

from pytest_sqlguard.sql import sql_fingerprint


class Query(NamedTuple):
    statement: str

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return {"statement": self.statement}

    def simplify(self):
        return Query(
            statement=sql_format(sql_fingerprint(self.statement), reindent=True),
        )


class QueryList(list):
    @classmethod
    def load_from(cls, path, name, lock_path=None):
        data = ReferenceFile(path, lock_path=lock_path).read_key(name)
        return cls(Query.from_dict(d) for d in data["queries"])

    def save_to(self, path, name, lock_path=None):
        value = {"queries": [query.to_dict() for query in self]}
        ReferenceFile(path, lock_path=lock_path).update_key(name, value)


class ReferenceFile:
    """
    Read/update reference queries by name in a YAML file

    Read and write access to the YAML file is protected by a lock file, to allow
    concurrent accesses by multiple processes (e.g. when using pytest-xdist).
    """

    def __init__(self, path, lock_path=None, lock_timeout=10):
        if not isinstance(path, Path):
            path = Path(path)
        self.path = path
        if lock_path is not None:
            self.lock = FileLock(lock_path, timeout=lock_timeout)
        else:
            self.lock = DummyLock()

    def read_key(self, name):
        with self.lock.acquire():
            data = self._load_data()
        return data[name]

    def update_key(self, name, value):
        with self.lock.acquire():
            data = self._load_data() if self.path.exists() else {}
            data[name] = value
            self._save_data(data)

    def _load_data(self):
        with self.path.open() as yaml_file:
            return yaml.safe_load(yaml_file) or {}

    def _save_data(self, data):
        with self.path.open(mode="w") as yaml_file:
            yaml.dump(data, yaml_file, Dumper=MultiLineDumper)


class MultiLineDumper(yaml.SafeDumper):
    """
    Pretty YAML dumping of multi-line strings
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_representer(str, self.multi_line_str_presenter)

    @staticmethod
    def multi_line_str_presenter(dumper, data):
        try:
            if len(data.splitlines()) > 1:
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        except TypeError:
            pass
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)


class DummyLock:
    def acquire(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return


class QueryRecorder:
    def __init__(self, session, format_queries=True, simplify_queries=True):
        self.engine = session.get_bind()
        self.session = session
        self.format_queries = format_queries
        self.simplify_queries = simplify_queries
        self._queries = QueryList()

    def start_recording(self):
        self._emit_any_pending_savepoint_statement()
        sqlalchemy.event.listen(
            self.engine,
            "before_cursor_execute",
            self._before_cursor_execute_hook,
        )

    def stop_recording(self):
        sqlalchemy.event.remove(
            self.engine,
            "before_cursor_execute",
            self._before_cursor_execute_hook,
        )

    def _emit_any_pending_savepoint_statement(self):
        self.session.execute(text("SELECT 1"))

    def _before_cursor_execute_hook(
        self,
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ):
        """
        See: https://docs.sqlalchemy.org/en/13/core/events.html#sqlalchemy.events.ConnectionEvents.before_cursor_execute
        """
        if self.format_queries:
            statement = sql_format(statement, reindent=True)
        query = Query(statement)
        if self.simplify_queries:
            query = query.simplify()
        # if need to understand where a query  is added uncomment this breakpoint
        # breakpoint()
        self.queries.append(query)

    @property
    def queries(self):
        return self._queries


class ReferenceQueryStorage:
    def __init__(
        self,
        path,
        name,
        create_missing_reference_data,
        fail_on_missing_reference_data,
        overwrite_reference_data,
        lock_path,
    ):
        self.path = path
        self.name = name
        self.fail_on_missing_reference_data = fail_on_missing_reference_data
        self.create_missing_reference_data = create_missing_reference_data
        self.overwrite_reference_data = overwrite_reference_data
        self.lock_path = lock_path

    def assert_matches(self, recorded_queries):
        """
        Assert that recorded queries match stored reference (if it exists)
        """
        reference_queries = self._load_reference_queries()
        if reference_queries:
            expected = Queries(reference_queries)
            result = Queries(recorded_queries)
            if self.overwrite_reference_data:
                if expected != result:
                    self.save_reference_to_disk(recorded_queries)
            else:
                assert expected == result
        else:
            if self.create_missing_reference_data:
                self.save_reference_to_disk(recorded_queries)
            if self.fail_on_missing_reference_data:
                raise MissingQueryReferenceData(self.path, self.name)

    def _load_reference_queries(self):
        try:
            return QueryList.load_from(self.path, self.name, self.lock_path)
        except (FileNotFoundError, KeyError):
            return None

    def save_reference_to_disk(self, recorded_queries):
        recorded_queries.save_to(self.path, self.name, self.lock_path)


class Queries(Counter):
    """
    We use the Counter class to represent queries as a multiset,
    so that the comparison does not depend on the order of queries.
    """


class record_queries:
    """
    Context manager to record database queries

    Optionally, save them to disk and compare them to a saved reference
    """

    def __init__(
        self,
        session,
        path=None,
        name=None,
        simplify_queries=True,
        create_missing_reference_data=True,
        fail_on_missing_reference_data=False,
        overwrite_reference_data=False,
        lock_path=None,
        enter_funcs=None,
    ):
        self.recorder = QueryRecorder(
            session=session,
            simplify_queries=simplify_queries,
        )
        self.enter_funcs = enter_funcs or []
        self.reference = None
        if (path is not None) and (name is not None):
            self.reference = ReferenceQueryStorage(
                path=path,
                name=name,
                create_missing_reference_data=create_missing_reference_data,
                fail_on_missing_reference_data=fail_on_missing_reference_data,
                overwrite_reference_data=overwrite_reference_data,
                lock_path=lock_path,
            )
        elif (path is None) ^ (name is None):  # XOR
            raise ValueError("Please provide both 'path' and 'name' parameters")

    def __enter__(self):
        for func in self.enter_funcs:
            func()
        self.recorder.start_recording()
        return self

    def __exit__(self, *exc_info):
        self.recorder.stop_recording()
        if self.reference:
            recorded_queries = self.recorder.queries
            self.reference.assert_matches(recorded_queries)


class MissingQueryReferenceData(AssertionError):
    def __init__(self, path, name):
        super().__init__(f"Missing query reference data '{name}' in '{path}'")
        self.path = path
        self.name = name
