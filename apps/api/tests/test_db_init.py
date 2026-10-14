"""init_db must not create tables behind Alembic's back (it broke `alembic upgrade` during development)."""

import sqlite3

import pytest

from app.core.config import get_settings
from app.db import session as db_session_module


@pytest.fixture
def sqlite_url(tmp_path, monkeypatch):
    path = tmp_path / "app.db"
    monkeypatch.setattr(get_settings(), "DATABASE_URL", f"sqlite+aiosqlite:///{path}")
    yield path
    db_session_module.engine = None


async def test_fresh_sqlite_database_gets_tables(sqlite_url):
    await db_session_module.init_db()
    await db_session_module.close_db()

    tables = {r[0] for r in sqlite3.connect(sqlite_url).execute("select name from sqlite_master where type='table'")}
    assert {"users", "tasks", "google_integrations"} <= tables


async def test_migration_managed_database_is_left_to_alembic(sqlite_url):
    con = sqlite3.connect(sqlite_url)
    con.execute("create table alembic_version (version_num varchar(32) primary key)")
    con.execute("insert into alembic_version values ('007_requirement_source')")
    con.commit()

    await db_session_module.init_db()
    await db_session_module.close_db()

    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    assert tables == {"alembic_version"}
