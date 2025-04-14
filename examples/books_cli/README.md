# 📚 Books CLI — Demo Project for pytest-sqlguard

This sample project showcases how to use [`pytest-sqlguard`](https://pypi.org/project/pytest-sqlguard/) in a realistic application. It includes a minimal CLI interface and a FastAPI web application for managing a books and authors database.

The main goal of this project is to demonstrate how `pytest-sqlguard` can help you detect and manage SQL changes in your codebase using snapshot testing.

---

## 🚀 Quick Start

This project uses [`uv`](https://docs.astral.sh/uv/) as the environment and task manager.

#### 1. Initialize the environment

```bash
uv init
```

---

## 🖥️ Command-Line Interface

The CLI is defined in the script [`books.py`](./books.py).

📌 To view CLI options:

```bash
uv run books.py --help
```

### CLI Commands

- 🏗️ Create the SQLite database (Run this at least once):

  ```bash
  uv run books.py init-db
  ```

- 🧹 Drop the database:

  ```bash
  uv run books.py drop-db
  ```

- ✍️ Manage authors (subcommand):

  ```bash
  uv run books.py authors
  ```

---

## 🌐 Web API (FastAPI)

You can run the FastAPI app located in [`books_cli/main.py`](./books_cli/main.py):

```bash
uv run fastapi dev books_cli/main.py
```

- API documentation is available at:
  👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Running Tests with pytest-sqlguard

The test suite illustrates how `pytest-sqlguard` detects unexpected SQL changes via snapshot testing.

Run the tests:

```bash
uv run pytest
```

Want to see `pytest-sqlguard` in action?

1. Open [`books_cli/operations/search.py`](./books_cli/operations/search.py)
2. Locate the function `list_books_by_author_name`
3. Uncomment the version that uses a SQL JOIN
4. Run tests again:

   ```bash
   uv run pytest
   ```

You should see SQL snapshot mismatches for both:

- [`tests/test_author.py`](./tests/test_author.py)
- [`tests/test_author_api.py`](./tests/test_author_api.py)

To resolve and update the snapshots to the new queries:

```bash
uv run pytest --sqlguard-overwrite
```

This will overwrite the following snapshot files:

- [`tests/test_author.queries.yaml`](./tests/test_author.queries.yaml)
- [`tests/test_author_api.queries.yaml`](./tests/test_author_api.queries.yaml)

---

## 🧰 Tech Stack

This project leverages:

- ⚡️ [FastAPI](https://fastapi.tiangolo.com/) – Web framework
- 🐍 [Typer](https://typer.tiangolo.com/) – CLI framework
- 🐘 [SQLAlchemy](https://www.sqlalchemy.org/) – ORM
- 🔎 [pytest](https://docs.pytest.org/en/stable/) – Test runner
- 🔐 [pytest-sqlguard](https://pypi.org/project/pytest-sqlguard/) – SQL snapshot testing
- 🚀 [uv](https://docs.astral.sh/uv/) – Python dependency and virtualenv manager
