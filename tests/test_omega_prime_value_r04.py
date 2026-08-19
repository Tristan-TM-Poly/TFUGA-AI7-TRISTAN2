from __future__ import annotations

import copy
import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from omega_prime_value_t.r03.canonical import sha256_hex
from omega_prime_value_t.r03.pocklington import compile_pocklington_certificate
from omega_prime_value_t.r04.benchmark import CHILD_PRIME, ROOT_PRIME, build_recursive_fixture, deterministic_benchmark
from omega_prime_value_t.r04.budget import BudgetLedger, ComputeBudgetPolicy, ComputeObservation, rank_work_items
from omega_prime_value_t.r04.external import import_external_artifact, verify_with_external_command
from omega_prime_value_t.r04.proof_dag import build_proof_graph, seal_graph, verify_proof_graph
from omega_prime_value_t.r04.residue import (
    candidate_survives,
    compile_proth_residue_program,
    filter_receipt,
    primes_up_to,
    segmented_survivors,
    verify_residue_program,
)
from omega_prime_value_t.r04.transparency import TransparencyLog, sign_checkpoint_openssl, verify_checkpoint


def recursive_graph():
    return build_proof_graph(build_recursive_fixture()[1])


def test_recursive_fixture_and_graph():
    assert CHILD_PRIME == 9 * 2**65 + 1
    assert ROOT_PRIME == 88 * CHILD_PRIME + 1
    graph = recursive_graph()
    assert ROOT_PRIME.bit_length() == 75
    assert len(graph.nodes) == 2 and graph.root in graph.nodes
    assert verify_proof_graph(graph) == (True, [])
    assert graph.to_dict() == recursive_graph().to_dict()


@pytest.mark.parametrize(
    ("mutation", "needle"),
    [
        (lambda p: p.update(sha256="0" * 64), "proof graph sha256 mismatch"),
        (lambda p: p.update(root="missing"), "proof graph root missing"),
        (lambda p: p["oak"].update(novelty_claimed=True), "may not claim novelty"),
    ],
)
def test_graph_top_level_tamper(mutation, needle):
    payload = recursive_graph().to_dict()
    mutation(payload)
    if payload.get("sha256") != "0" * 64:
        payload = seal_graph(payload)
    valid, errors = verify_proof_graph(payload)
    assert not valid and any(needle in error for error in errors)


def test_graph_missing_child_cycle_unreachable_and_id_mismatch():
    base = recursive_graph().to_dict()
    root = base["root"]
    child = next(iter(base["nodes"][root]["child_refs"].values()))

    missing = copy.deepcopy(base)
    del missing["nodes"][child]
    assert any("missing node" in e for e in verify_proof_graph(seal_graph(missing))[1])

    cycle = copy.deepcopy(base)
    cycle["nodes"][child]["child_refs"] = {"2": root}
    assert any("cycle detected" in e for e in verify_proof_graph(seal_graph(cycle))[1])

    unreachable = copy.deepcopy(base)
    extra = copy.deepcopy(unreachable["nodes"][root])
    extra["node_id"] = "unreachable"
    unreachable["nodes"]["unreachable"] = extra
    assert any("unreachable proof nodes" in e for e in verify_proof_graph(seal_graph(unreachable))[1])

    mismatch = copy.deepcopy(base)
    mismatch["nodes"][root]["node_id"] = "wrong"
    assert any("node key/id mismatch" in e for e in verify_proof_graph(seal_graph(mismatch))[1])


def test_graph_extra_ref_and_tampered_child():
    payload = recursive_graph().to_dict()
    payload["nodes"][payload["root"]]["child_refs"]["99991"] = payload["root"]
    assert any("unused child refs" in e for e in verify_proof_graph(seal_graph(payload))[1])

    child = compile_pocklington_certificate(CHILD_PRIME, {2: 65}).to_dict()
    root = compile_pocklington_certificate(
        ROOT_PRIME, {2: 3, 11: 1, CHILD_PRIME: 1}, child_certificates={CHILD_PRIME: child}
    ).to_dict()
    root["factors"][-1]["child_certificate"]["sha256"] = "f" * 64
    assert any("certificate sha256 mismatch" in e for e in verify_proof_graph(build_proof_graph(root))[1])


@pytest.mark.parametrize(
    ("limit", "expected"),
    [(0, ()), (1, ()), (2, (2,)), (10, (2, 3, 5, 7)), (20, (2, 3, 5, 7, 11, 13, 17, 19))],
)
def test_primes(limit, expected):
    assert primes_up_to(limit) == expected


def test_residue_program_integrity_and_tamper():
    program = compile_proth_residue_program(8, 10, prime_bound=97)
    assert verify_residue_program(program) == (True, [])
    assert program.to_dict() == compile_proth_residue_program(8, 10, prime_bound=97).to_dict()

    bad_hash = program.to_dict()
    bad_hash["sha256"] = "0" * 64
    assert "residue program sha256 mismatch" in verify_residue_program(bad_hash)[1]

    bad_rule = program.to_dict()
    bad_rule["rules"][0]["forbidden_residue"] ^= 1
    bad_rule["sha256"] = ""
    bad_rule["sha256"] = sha256_hex(bad_rule)
    assert "residue rules do not match compiler output" in verify_residue_program(bad_rule)[1]


@pytest.mark.parametrize("bounds", [(0, 3), (5, 4)])
def test_bad_exponent_interval(bounds):
    with pytest.raises(ValueError):
        compile_proth_residue_program(*bounds)


def test_bad_prime_bound_and_outside_exponent():
    with pytest.raises(ValueError):
        compile_proth_residue_program(1, 1, prime_bound=2)
    program = compile_proth_residue_program(8, 9, prime_bound=31)
    with pytest.raises(ValueError, match="outside"):
        candidate_survives(program, 10, 1)


def test_candidate_filter_matches_direct_divisibility():
    program = compile_proth_residue_program(12, 12, prime_bound=97)
    divisors = [p for p in primes_up_to(97) if p != 2]
    for k in range(1, 512, 2):
        assert candidate_survives(program, 12, k) is all((k * 2**12 + 1) % p for p in divisors)
    assert not candidate_survives(program, 12, 0)
    assert not candidate_survives(program, 12, 2)
    assert not candidate_survives(program, 12, 2**12)


@pytest.mark.parametrize("segment_size", [1, 2, 7, 64, 113, 1024])
def test_segmented_filter_equals_naive(segment_size):
    program = compile_proth_residue_program(12, 12, prime_bound=97)
    actual = tuple(segmented_survivors(program, 12, 1, 2047, segment_size=segment_size))
    expected = tuple(k for k in range(1, 2048, 2) if candidate_survives(program, 12, k))
    assert actual == expected


@pytest.mark.parametrize("args", [(1, 100, 0), (100, 1, 10)])
def test_segment_validation(args):
    program = compile_proth_residue_program(8, 8, prime_bound=31)
    with pytest.raises(ValueError):
        tuple(segmented_survivors(program, 8, args[0], args[1], segment_size=args[2]))


def test_filter_receipt():
    receipt = filter_receipt(compile_proth_residue_program(12, 12, prime_bound=97), 12, 1, 2047, segment_size=113)
    assert receipt["odd_candidates"] == 1024
    assert receipt["survivors"] == len(receipt["survivor_values"])
    assert receipt["rejected"] + receipt["survivors"] == 1024
    assert receipt["oak"]["primality_claimed"] is False


def policy():
    return ComputeBudgetPolicy(100.0, 1000, 1.0, 10.0, 0.1, 2)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ComputeBudgetPolicy(-1, 1, 1, 1),
        lambda: ComputeBudgetPolicy(1, -1, 1, 1),
        lambda: ComputeBudgetPolicy(1, 1, 1, 1, 1.0),
        lambda: ComputeBudgetPolicy(1, 1, 1, 1, 0.1, 0),
        lambda: ComputeObservation("", "x", 1, 1, 1, 1, 1),
        lambda: ComputeObservation("x", "x", -1, 1, 1, 1, 1),
    ],
)
def test_budget_model_validation(factory):
    with pytest.raises(ValueError):
        factory()


def test_budget_report_duplicate_and_backpressure():
    ledger = BudgetLedger(policy())
    first = ComputeObservation("a", "product", 10, 100, 0.1, 1, 5)
    ledger.record(first)
    report = ledger.report()
    assert report["totals"]["cpu_seconds"] == 10
    assert report["effective_limits_after_reserve"]["cpu_seconds"] == 90
    assert report["state"] == "open" and report["oak"]["financial_return_claimed"] is False
    with pytest.raises(ValueError, match="duplicate work_id"):
        ledger.record(first)
    pressure = BudgetLedger(policy())
    pressure.record(ComputeObservation("p", "x", 75, 0, 0, 0, 1))
    assert pressure.report()["state"] == "backpressure"


@pytest.mark.parametrize(
    ("observation", "key"),
    [
        (ComputeObservation("cpu", "x", 91, 0, 0, 0, 1), "cpu_seconds"),
        (ComputeObservation("candidates", "x", 0, 901, 0, 0, 1), "candidates"),
        (ComputeObservation("energy", "x", 0, 0, 0.91, 0, 1), "energy_kwh"),
        (ComputeObservation("cost", "x", 0, 0, 0, 9.1, 1), "cost_cad"),
    ],
)
def test_budget_reserve_boundaries(observation, key):
    allowed, reasons = BudgetLedger(policy()).can_accept(observation)
    assert not allowed and any(key in reason for reason in reasons)


def test_rank_work_items():
    ranked = rank_work_items([
        {"work_id": "b", "expected_evidence": 10, "expected_cpu_seconds": 9},
        {"work_id": "a", "expected_evidence": 10, "expected_cpu_seconds": 9},
        {"work_id": "c", "expected_evidence": 1, "expected_cpu_seconds": 100},
    ])
    assert [item["work_id"] for item in ranked] == ["a", "b", "c"]


@pytest.mark.parametrize("format", ["primo", "ecpp", "pocklington-external", "generic-primality-certificate"])
def test_external_import_formats(format):
    receipt = import_external_artifact(b"fixture", format=format, source_label="test")
    assert receipt.format == format and receipt.oak["artifact_import_is_not_proof_verification"] is True


@pytest.mark.parametrize("format,label", [("unknown", "test"), ("primo", "")])
def test_external_import_rejections(format, label):
    with pytest.raises(ValueError):
        import_external_artifact(b"x", format=format, source_label=label)


def verifier(tmp_path: Path, marker="PRIME", code=0):
    path = tmp_path / "verifier.py"
    path.write_text(
        "#!/usr/bin/env python3\nimport pathlib,sys\n"
        f"print('{marker}' if pathlib.Path(sys.argv[1]).read_bytes() else 'EMPTY')\nraise SystemExit({code})\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


@pytest.mark.parametrize(("marker", "code", "expected"), [("PRIME", 0, True), ("COMPOSITE", 0, False), ("PRIME", 3, False)])
def test_external_verifier_outcomes(tmp_path, marker, code, expected):
    data = b"certificate"
    imported = import_external_artifact(data, format="ecpp", source_label="fixture")
    receipt = verify_with_external_command(data, imported, executable=verifier(tmp_path, marker, code))
    assert receipt.verified_by_declared_tool is expected
    assert receipt.oak["shell_invocation_used"] is False
    assert receipt.arguments == ("{artifact}",)


def test_external_verifier_guards(tmp_path):
    imported = import_external_artifact(b"a", format="ecpp", source_label="fixture")
    with pytest.raises(ValueError, match="do not match"):
        verify_with_external_command(b"b", imported, executable=verifier(tmp_path))
    with pytest.raises(ValueError):
        verify_with_external_command(b"a", imported, executable=tmp_path / "missing")
    with pytest.raises(ValueError, match="placeholder"):
        verify_with_external_command(b"a", imported, executable=verifier(tmp_path), arguments=("fixed",))


@pytest.mark.parametrize("timeout", [0, -1, 301])
def test_external_timeout_guard(tmp_path, timeout):
    imported = import_external_artifact(b"a", format="ecpp", source_label="fixture")
    with pytest.raises(ValueError):
        verify_with_external_command(b"a", imported, executable=verifier(tmp_path), timeout_seconds=timeout)


def test_log_chain_checkpoint_and_determinism(tmp_path):
    outputs = []
    for name in ("a.sqlite3", "b.sqlite3"):
        with TransparencyLog(tmp_path / name) as log:
            first = log.append("a", {"x": 1})
            second = log.append("b", {"x": 2})
            assert first.sequence == 0 and second.previous_hash == first.entry_hash
            assert log.verify_chain() == (True, [])
            checkpoint = log.checkpoint(tree_size=2, created_at_utc="2026-08-03T00:00:00+00:00")
            assert verify_checkpoint(checkpoint, log.entries()) == (True, [])
            outputs.append([entry.to_dict() for entry in log.entries()])
    assert outputs[0] == outputs[1]


def test_log_input_guards(tmp_path):
    with TransparencyLog(tmp_path / "log.sqlite3") as log:
        with pytest.raises(ValueError):
            log.append("", 1)
        log.append("x", 1)
        with pytest.raises(ValueError):
            log.entries(limit=-1)
        with pytest.raises(ValueError):
            log.checkpoint(tree_size=0, created_at_utc="2026-08-03T00:00:00+00:00")
        with pytest.raises(ValueError, match="ISO-8601"):
            log.checkpoint(created_at_utc="bad")


@pytest.mark.parametrize(("column", "value", "needle"), [
    ("payload_json", '{"x":2}', "payload hash mismatch"),
    ("previous_hash", "f" * 64, "previous hash mismatch"),
])
def test_log_tamper(tmp_path, column, value, needle):
    with TransparencyLog(tmp_path / "log.sqlite3") as log:
        log.append("a", {"x": 1})
        if column == "previous_hash":
            log.append("b", {"x": 2})
            sequence = 1
        else:
            sequence = 0
        log.connection.execute(f"UPDATE entries SET {column} = ? WHERE sequence = ?", (value, sequence))
        log.connection.commit()
        assert any(needle in error for error in log.verify_chain()[1])


def test_checkpoint_tamper_and_missing_prefix(tmp_path):
    with TransparencyLog(tmp_path / "log.sqlite3") as log:
        log.append("x", 1)
        checkpoint = log.checkpoint(created_at_utc="2026-08-03T00:00:00+00:00")
        assert "checkpoint prefix unavailable" in verify_checkpoint(checkpoint, [])[1]
        payload = checkpoint.to_dict()
        payload["merkle_root"] = "0" * 64
        errors = verify_checkpoint(payload, log.entries())[1]
        assert "checkpoint sha256 mismatch" in errors and "checkpoint Merkle root mismatch" in errors


def keypair(tmp_path, prefix="key"):
    private = tmp_path / f"{prefix}-private.pem"
    public = tmp_path / f"{prefix}-public.pem"
    subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(private)], check=True)
    subprocess.run(["openssl", "pkey", "-in", str(private), "-pubout", "-out", str(public)], check=True)
    return private, public


@pytest.mark.skipif(shutil.which("openssl") is None, reason="OpenSSL unavailable")
def test_ed25519_round_trip_wrong_key_and_bound_oak(tmp_path):
    private, public = keypair(tmp_path)
    _, wrong_public = keypair(tmp_path, "wrong")
    with TransparencyLog(tmp_path / "log.sqlite3") as log:
        log.append("fixture", 1)
        signed = sign_checkpoint_openssl(
            log.checkpoint(created_at_utc="2026-08-03T00:00:00+00:00"),
            private_key=private,
            public_key=public,
        )
        assert verify_checkpoint(signed, log.entries(), public_key=public) == (True, [])
        assert "public key fingerprint mismatch" in verify_checkpoint(signed, log.entries(), public_key=wrong_public)[1]
        tampered = signed.to_dict()
        tampered["oak"]["novelty_claimed"] = True
        tampered["sha256"] = ""
        tampered["sha256"] = sha256_hex(tampered)
        assert "checkpoint signature verification failed" in verify_checkpoint(tampered, log.entries(), public_key=public)[1]


def test_benchmark_invariants_and_determinism():
    payload = deterministic_benchmark()
    assert payload == deterministic_benchmark()
    assert payload["status"].endswith("R0_4")
    assert payload["recursive_proof"]["valid"] is True and payload["recursive_proof"]["root_bits"] == 75
    assert len(payload["recursive_proof"]["graph"]["nodes"]) == 2
    assert payload["residue_compiler"]["valid"] is True
    assert payload["transparency"]["chain_valid"] is True and payload["transparency"]["checkpoint_valid"] is True
    assert payload["budget"]["state"] == "open"
    assert payload["external_adapter"]["status"] == "IMPORTED_UNVERIFIED_EXTERNAL_ARTIFACT_R0_4"
    assert all(value is False for value in payload["claims"].values())


def run_cli(root, *args):
    return subprocess.run([sys.executable, "-m", "omega_prime_value_t.r04", *map(str, args)], cwd=root, check=False)


def test_cli_benchmark_graph_and_residue(tmp_path):
    root_dir = Path(__file__).parents[1]
    benchmark = tmp_path / "benchmark.json"
    assert run_cli(root_dir, "benchmark", "--output", benchmark).returncode == 0

    certificate = tmp_path / "certificate.json"
    graph = tmp_path / "graph.json"
    verification = tmp_path / "verification.json"
    certificate.write_text(json.dumps(build_recursive_fixture()[1]))
    assert run_cli(root_dir, "build-proof-graph", certificate, "--output", graph).returncode == 0
    assert run_cli(root_dir, "verify-proof-graph", graph, "--output", verification).returncode == 0
    assert json.loads(verification.read_text()) == {"errors": [], "valid": True}

    program = tmp_path / "program.json"
    receipt = tmp_path / "receipt.json"
    assert run_cli(root_dir, "compile-residues", "--exponent-min", 8, "--exponent-max", 8, "--prime-bound", 31, "--output", program).returncode == 0
    assert run_cli(root_dir, "scan-residues", program, "--exponent", 8, "--k-start", 1, "--k-stop", 127, "--output", receipt).returncode == 0
    assert json.loads(receipt.read_text())["odd_candidates"] == 64
