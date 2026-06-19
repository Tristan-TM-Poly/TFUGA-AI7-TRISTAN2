from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OMEGA_16N = ROOT / "experiments" / "omega_16n"
if str(OMEGA_16N) not in sys.path:
    sys.path.insert(0, str(OMEGA_16N))

from omega_16n import (
    enumerate_paths,
    hex_word_to_int,
    int_to_hex_word,
    oak_adjusted_score,
    path_count,
    symbolic_summary,
    top_k_paths,
)


def test_path_count_is_16_power_n():
    assert path_count(0) == 1
    assert path_count(1) == 16
    assert path_count(2) == 256
    assert path_count(3) == 4096


def test_fixed_length_hex_encoding_round_trip():
    depth = 4
    for value in [0, 1, 15, 16, 255, 4096, 16**depth - 1]:
        word = int_to_hex_word(value, depth)
        assert len(word) == depth
        assert hex_word_to_int(word) == value


def test_enumerate_paths_respects_limit():
    paths = enumerate_paths(4, limit=17)
    assert len(paths) == 17
    assert paths[0].word == "0000"
    assert paths[-1].word == "0010"


def test_top_k_paths_returns_scored_frontier():
    frontier = top_k_paths(3, k=8)
    assert len(frontier) == 8
    assert all("oak_adjusted_score" in row for row in frontier)
    assert all(len(row["word"]) == 3 for row in frontier)


def test_negative_memory_penalizes_known_bad_patterns():
    assert oak_adjusted_score("FFFF") < oak_adjusted_score("48CD")
    assert oak_adjusted_score("AAAA") < oak_adjusted_score("48CD")


def test_symbolic_summary_avoids_large_full_materialization():
    summary = symbolic_summary(5, k=4, sample_limit=64)
    assert summary["raw_path_count"] == 16**5
    assert summary["materialized_for_frontier"] == 64
    assert summary["full_materialization_allowed"] is False
    assert len(summary["top_k_frontier"]) == 4
    guardrails = "\n".join(summary["guardrails"])
    assert "Generation is not proof" in guardrails
