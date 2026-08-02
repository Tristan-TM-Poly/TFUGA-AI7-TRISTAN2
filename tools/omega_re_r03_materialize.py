"""Fail-closed materializer for the Ω-RE-T∞ R0.3 verified source payload."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

PART_SHA256 = (
    "711ff36646ab165b028fdbaf25b0fcf4d06e881b27253b2a8a280a6de14ea7fe",
    "2893240e06b8b8286f6e1f7bf6112329a9ded1d87496a71a053dfa4f72c09c48",
    "942ec1680fc4f8139c660a5f41bb3b98b6efce643ed66e37107e4b64a9b1acd4",
    "701c932063a90816e2c0a3ab1a72f234903f289fa7ebe1633639c0f4e4a7f0ef",
    "dbbb6b24961c632239d8943748261acfc9709b6913c7da76c17c5567b94c6be0",
    "2a037396893c21d305b4f855e1f22bb59be30ce1c939756411dbd7ae76f54629",
)
ARCHIVE_SHA256 = "b1eb6be9785649c6dc9b7fb1d8c85218ecf55b9fb296cc4404bd2940e3d9ad62"
FILE_SHA256 = {
    "docs/omega-re-t/FOUNDATION_R0_3.md": "c7d29f107dc001c1c28dcaaf50ecd68905a7d549e0b737d33d77393b3d7f569b",
    "omega_re_t/active_learning.py": "bffe953f6dcd55e550552221e32d3d9560d168b588e73d6ac6bb87da61762752",
    "omega_re_t/causal.py": "4a99ea15a7efeec02c88b650630971bb984f8d0815b168532e1c48bde527e5e1",
    "omega_re_t/cleanroom_agents.py": "83599ff242e6aeb1aa287dbffe03c72a691d1b6acac86bef7d161baf461623d2",
    "omega_re_t/genealogy.py": "2905bfbb212f18ee95cc9e452accf84e2a0fb42eee6682cc5cb006d28e4e6633",
    "omega_re_t/grammar.py": "5055fec223b04c6ac0a436102bfbfb813127c97cdee8b5a11213e813bd8366ae",
    "omega_re_t/hybrid.py": "f522263b91fc75ba0015f5173de6a07ee5f3f5ff2698a28311ca1c5f0affd246",
    "omega_re_t/nondeterministic.py": "cc602f7a79c719aa36d3453801c0beb82262305e06e8628d7524d818c5bc3be5",
    "omega_re_t/protocol.py": "7edaa5bc99c710a890ff3aaec6fb5bc9ceaa2d924b34723e1e1e348f5683c069",
    "omega_re_t/r03_cli.py": "1e43aed500737db798e22bf3f49cec8ebe337524eb7a9dfcde896f875e2b51d0",
    "omega_re_t/r03_frontier.py": "86410de8c4d061477b98201306cb8b7844dd8a76dcdd7850daa10aed708fa8b5",
    "omega_re_t/sharding.py": "cec25bc248615236c65d49100001983e53cbdb7740ee8b2a1b03c93ff7631d88",
    "schemas/omega-re-r03.schema.json": "8641243a4f2e69c6ffdc09e3737b58c2e87d260c9a4106a0311ff00e2b910bae",
    "tests/test_r03_active_nd.py": "812b5fc30776408fdfa40650baed8d8df8003efb618ddd5c76a38273c13ceafa",
    "tests/test_r03_causal_grammar_protocol.py": "e732344a2932a0b46b98329e17ce4faddd346da965dada32e5925cafca7e81f2",
    "tests/test_r03_hybrid_genealogy_cleanroom.py": "8219d9177c758e7ca028602de82d01af4142c6bdef15902aa5fb58b4c91766c8",
    "tests/test_r03_sharding_frontier_cli.py": "5a9fb18549e27d06ce09f828d44f37b66d6646761f51ca513a78b6e02fd0324d",
}
CLI_LINES = (
    'omega-re-r03 = "omega_re_t.r03_cli:main"',
    'omega-re-re1024 = "omega_re_t.r03_frontier:main"',
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload(root: Path) -> bytes:
    chunks = []
    for index, expected in enumerate(PART_SHA256):
        data = (root / "tools" / "omega_re_r03_payload" / f"part{index:02d}.txt").read_bytes()
        if sha256(data) != expected:
            raise RuntimeError(f"payload part {index:02d} SHA-256 mismatch")
        chunks.append(data)
    try:
        archive = base64.b85decode(b"".join(chunks))
    except ValueError as exc:
        raise RuntimeError("invalid base85 payload") from exc
    if sha256(archive) != ARCHIVE_SHA256:
        raise RuntimeError("archive SHA-256 mismatch")
    return archive


def validate_member(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or name.endswith("/"):
        raise RuntimeError(f"unsafe archive member: {name}")


def archive_files(root: Path) -> dict[str, bytes]:
    archive = payload(root)
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = tuple(bundle.namelist())
        for name in names:
            validate_member(name)
        if set(names) != set(FILE_SHA256):
            missing = sorted(set(FILE_SHA256) - set(names))
            extra = sorted(set(names) - set(FILE_SHA256))
            raise RuntimeError(f"archive allowlist mismatch: missing={missing}, extra={extra}")
        files = {name: bundle.read(name) for name in names}
    for name, data in files.items():
        if sha256(data) != FILE_SHA256[name]:
            raise RuntimeError(f"file SHA-256 mismatch: {name}")
    return files


def patch_pyproject(root: Path, *, write: bool) -> bool:
    path = root / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    missing = [line for line in CLI_LINES if line not in text]
    if not missing:
        return False
    marker = "\n[tool.pytest.ini_options]"
    if marker not in text:
        raise RuntimeError("pyproject insertion marker is missing")
    replacement = "\n" + "\n".join(missing) + marker
    updated = text.replace(marker, replacement, 1)
    if write:
        path.write_text(updated, encoding="utf-8")
    return True


def extract(root: Path, *, force: bool = False) -> list[str]:
    files = archive_files(root)
    written = []
    for name, data in files.items():
        target = root / name
        if target.exists() and target.read_bytes() != data and not force:
            raise RuntimeError(f"refusing to overwrite divergent file: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written.append(name)
    if patch_pyproject(root, write=True):
        written.append("pyproject.toml")
    return sorted(written)


def verify(root: Path, *, require_extracted: bool = False) -> dict[str, object]:
    files = archive_files(root)
    extracted = 0
    for name, data in files.items():
        target = root / name
        if target.exists():
            if target.read_bytes() != data:
                raise RuntimeError(f"extracted file differs from payload: {name}")
            extracted += 1
        elif require_extracted:
            raise RuntimeError(f"required extracted file is missing: {name}")
    pyproject_needs_patch = patch_pyproject(root, write=False)
    if require_extracted and pyproject_needs_patch:
        raise RuntimeError("pyproject CLI entries are missing")
    return {
        "schema": "omega-re-r03-materializer/1.0",
        "archive_sha256": ARCHIVE_SHA256,
        "payload_parts": len(PART_SHA256),
        "allowlisted_files": len(FILE_SHA256),
        "extracted_files": extracted,
        "pyproject_needs_patch": pyproject_needs_patch,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--require-extracted", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    written = extract(root, force=args.force) if args.extract else []
    report = verify(root, require_extracted=args.require_extracted or args.extract)
    report["written"] = written
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
