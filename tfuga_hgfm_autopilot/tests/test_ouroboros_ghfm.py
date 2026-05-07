import asyncio
from pathlib import Path

from tfuga_hgfm_autopilot.scripts.ouroboros_ghfm import (
    GHFMConfig,
    append_merkle_block,
    compute_merkle_hash,
    run_ouroboros,
    seconds_since_interaction,
    touch_interaction_file,
)


def test_compute_merkle_hash_is_stable() -> None:
    first = compute_merkle_hash("previous", "2026-05-07T00:00:00+00:00", "Validated")
    second = compute_merkle_hash("previous", "2026-05-07T00:00:00+00:00", "Validated")
    assert first == second
    assert len(first) == 64


def test_append_merkle_block_writes_log(tmp_path: Path) -> None:
    log = tmp_path / "Yggdrasil_Merkle.log"
    new_hash = append_merkle_block(log, "GENESIS", "Validated")
    text = log.read_text(encoding="utf-8")
    assert new_hash in text
    assert "Validated" in text


def test_touch_and_seconds_since_interaction(tmp_path: Path) -> None:
    path = tmp_path / "ms33_telemetry.log"
    assert seconds_since_interaction(path) is None
    touch_interaction_file(path)
    assert seconds_since_interaction(path) is not None


def test_run_ouroboros_one_cycle(tmp_path: Path) -> None:
    config = GHFMConfig.from_root(tmp_path, max_cycles=1)
    asyncio.run(run_ouroboros(config))
    assert config.merkle_log.exists()
    assert config.interaction_file.exists()
