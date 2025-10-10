from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine


def test_init_db_creates_expected_tables(tmp_path: Path) -> None:
    """Create a temporary SQLite file and assert expected tables exist.

    This test is written first (TDD); it fails until the storage layer is in place.
    """
    db_path = tmp_path / "test_photo_archivist.db"

    # Import here so tests that don't touch storage won't fail to import the package
    from photo_archivist import storage

    # Create engine for the given path and initialize the DB
    engine = storage.get_engine(path=str(db_path))
    assert isinstance(engine, sa.engine.Engine)

    # init_db should create the file and materialize tables
    storage.init_db(engine=engine)

    inspector = sa.inspect(engine)
    tables = set(inspector.get_table_names())

    expected = {"photo_items", "shortlist_entries", "runs", "orders"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"

    # Ensure primary keys exist for each expected table
    for table in expected:
        pk = inspector.get_pk_constraint(table)
        assert pk and pk.get("constrained_columns"), f"Table {table} has no primary key"

    # get_session should yield sessions bound to the same engine
    with storage.get_session() as session:
        assert hasattr(session, "bind")
        assert isinstance(session.bind, Engine)
        # Session.bind may be None; ensure it's the same engine when present
        if session.bind is not None:
            assert session.bind.url == engine.url


@pytest.mark.parametrize("path_arg", [None, "memory"])
def test_get_engine_variants(path_arg):
    """Smoke test get_engine with different inputs to ensure it returns an Engine."""
    from photo_archivist import storage

    engine = storage.get_engine(path=path_arg)
    assert isinstance(engine, sa.engine.Engine)
