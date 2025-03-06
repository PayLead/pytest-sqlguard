# pytest-sqlguard 🔍🛡️

[![pytest](https://img.shields.io/badge/pytest-extension-blue)](https://docs.pytest.org/en/latest/)
[![Python](https://img.shields.io/pypi/v/pytest-sqlguard)](https://pypi.org/project/pytest-sqlguard/)
<!-- ![GitHub License](https://img.shields.io/github/license/PayLead/pytest-sqlguard) -->

---

`pytest-sqlguard` is a pytest plugin that helps you safeguard your SQLAlchemy queries against unintended changes.
It records all database queries executed during tests and compares them against previously recorded "reference" queries,
alerting you to any differences or regressions that may impact SQL functionality or performance.

✅ Easily detect unintended database query changes, regressions

✅ Prevent accidental database performance degradation

✅ Simple integration with SQLAlchemy & pytest


## Installation 📦

```bash
uv add pytest-sqlguard
```

## Usage 🚀

Configure your fixture as you like and then it can be as simple as:

```python
def test_your_database_logic(sqlguard, session):
    with sqlguard(session):
        test_client.get("/users/random_id")
```

When you run the test for the first time, pytest-sqlguard records all queries executed during the test and stores them as "reference data".

On subsequent test runs, it compares current queries against the reference, alerting you if any differences are found.
The stored data is in a _yaml_ file named as your test file but with the `.queries.yaml` extension:

```yaml
test_your_database_logic:
  queries:
  - statement: |-
      SELECT ...
      FROM public.users
      WHERE public.users.id = %(pk_1)s::UUID
```

## Command Line Options ⚙️

The extension provides two configurable behaviors (that defaults to False for both of them)
1. **Fail Missing**: Fail if the queries are missing in the reference file.
2. **Overwrite**: If set to True, it will overwrite the reference query

You can add option flag to pytest to control those behaviors:

```python
# In your conftest.py
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
```

For example, to trigger an error if the stored reference queries are missing, run:

```bash
pytest --sqlguard-fail-missing
```

To update reference queries after intended SQL changes, use:

```bash
pytest --sqlguard-overwrite
```

## Configuring the Fixture in Tests ⚗️
You need to define your fixture in your `conftest.py` file.
Here is an example of a working fixture:
```python
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
```

You can also use the assert representation we created to show the differences:

```python
# In conftest.py
from pytest_sqlguard.sqlguard import assertrepr_compare

def pytest_assertrepr_compare(config, op, left, right):
    return assertrepr_compare(config, op, left, right)
```

## Contributing 🤝

Issues, feature requests, and contributions are warmly welcomed! Feel free to open a pull request or submit an issue.

## License 📜

`pytest-sqlguard` is distributed under the MIT license. See [LICENSE](./LICENSE.md) for details.
