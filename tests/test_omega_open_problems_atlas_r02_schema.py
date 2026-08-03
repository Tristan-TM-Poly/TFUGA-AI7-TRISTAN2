from __future__ import annotations

from pathlib import Path

import pytest

from omega_open_problems_atlas.r02.store import AtlasStore, EXPECTED_TABLE_COLUMNS


def test_sqlite_schema_contract_matches_declared_columns(tmp_path: Path) -> None:
    with AtlasStore(tmp_path / "atlas.sqlite3") as store:
        observed = store.validate_schema_contract()
        assert observed == EXPECTED_TABLE_COLUMNS
        assert store.table_columns("leads") == (
            "lead_id",
            "source_id",
            "statement_hash",
            "canonical_hash",
            "status",
            "independently_checked_open",
            "solution_claimed",
            "payload",
        )


def test_sqlite_schema_contract_rejects_unknown_table(tmp_path: Path) -> None:
    with AtlasStore(tmp_path / "atlas.sqlite3") as store:
        with pytest.raises(ValueError):
            store.table_columns("not_an_atlas_table")
