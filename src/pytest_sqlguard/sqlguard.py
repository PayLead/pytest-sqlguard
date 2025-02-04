from difflib import unified_diff
from functools import partial
from pathlib import Path

# from core.models.db import session as db_session
# from core.tasks import task_manager
from pytest_sqlguard.perf_rec import Queries, record_queries

# Optional dependency to enable colored output in record_db_queries()
try:
    from termcolor import colored
except ImportError:

    def colored(text, color=None):
        return text


cyan = partial(colored, color="cyan")
green = partial(colored, color="green")
red = partial(colored, color="red")


def build_unified_diff(reference, recorded):
    return unified_diff(
        reference.splitlines(),
        recorded.splitlines(),
        fromfile="reference query (YAML)",
        tofile="recorded query (test)",
    )


def changed_query(reference, recorded):
    lines = ["", cyan("Changes were found in the following query:"), ""]
    lines.extend(build_unified_diff(reference.statement, recorded.statement))
    return lines


def missing_queries(only_in_reference):
    lines = [""]
    missing = [query.statement for query in only_in_reference]
    nb_missing = len(missing)
    suffix = "ies" if nb_missing > 1 else "y"
    lines.append(cyan(f"{nb_missing} expected quer{suffix} not seen during tests:"))
    for index, statement in enumerate(missing, 1):
        lines.append("")
        lines.append(cyan(f"  {index})"))
        lines.extend(red("    " + line) for line in statement.splitlines())
    return lines


def unexpected_queries(only_in_recorded):
    lines = [""]
    unexpected = [query.statement for query in only_in_recorded]
    nb_unexpected = len(unexpected)
    suffix = "ies" if nb_unexpected > 1 else "y"
    lines.append(cyan(f"{nb_unexpected} unexpected quer{suffix} recorded during tests:"))
    for index, statement in enumerate(unexpected, 1):
        lines.append("")
        lines.append(cyan(f"  {index})"))
        lines.extend(green("    " + line) for line in statement.splitlines())
    return lines


def assertrepr_compare(config, op, left, right):
    if isinstance(left, Queries) and isinstance(right, Queries) and op == "==":
        lines = ["left == right failed."]

        only_in_reference = list((left - right).elements())
        only_in_recorded = list((right - left).elements())

        if len(only_in_reference) == len(only_in_recorded) == 1:
            lines.extend(changed_query(only_in_reference[0], only_in_recorded[0]))
        else:
            if only_in_reference:
                lines.extend(missing_queries(only_in_reference))
            if only_in_recorded:
                lines.extend(unexpected_queries(only_in_recorded))

        return lines


def replace_extension(path, new_ext):
    return path.parent / Path(path.stem + ".queries.yaml")


def sqlguard(
    request,
    tmp_path_factory,
    fail_on_missing_reference_data: bool = False,
    overwrite_reference_data: bool = False,
    expire_all=True,
):
    """
    Fixture to record and check database queries.

    Use it as a context manager:

        with record_db_queries():
            ...

    If you want to use it multiple times in the same test, add a key param:

        with record_db_queries(key="first"):
            ...

        with record_db_queries(key="second"):
            ...

    Sometimes you may want to ignore and overwrite already existing reference data:

        with record_db_queries(overwrite=True):
            ...

    You may also use the `--overwrite-queries-reference-data` pytest flag, or the
    `RECORD_DB_QUERIES_OVERWRITE` environment variable to enable this globally.

    If you want to record the complete queries, without removing constants or
    parameters to the `SELECT` clause, set `simplify` to `False`:

        with record_db_queries(simplify=False):
            ...

    If expire_all is True (Default), the SQLAlchemy session will expire all its current objects before
    running the recorder.


    """

    test_filename, test_name = request.node.nodeid.split("::", maxsplit=1)
    test_filename = Path(test_filename)
    reference_data_filename = replace_extension(test_filename, ".queries.yaml")

    # When using pytest-xdist, use a file lock in a temp directory shared by all workers
    lock_path = None
    if request.config.pluginmanager.has_plugin("xdist"):
        shared_tmp_dir = tmp_path_factory.getbasetemp().parent
        lock_path = shared_tmp_dir / test_filename.with_suffix(".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)

    def record_queries_for_current_test(
        db_session,
        key=None,
        overwrite=None,
        simplify=True,
        enter_funcs=None,
        expire_all=expire_all,
    ):
        enter_funcs = enter_funcs or []
        if overwrite is None:
            overwrite = overwrite_reference_data
        name = test_name
        if key is not None:
            name = f"{name}::{key}"
        if expire_all:
            enter_funcs.append(db_session.expire_all)
        return record_queries(
            db_session,
            path=reference_data_filename,
            name=name,
            fail_on_missing_reference_data=fail_on_missing_reference_data,
            overwrite_reference_data=overwrite_reference_data,
            simplify_queries=simplify,
            lock_path=lock_path,
            enter_funcs=enter_funcs,
        )

    return record_queries_for_current_test
