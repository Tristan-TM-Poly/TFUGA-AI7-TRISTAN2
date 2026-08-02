"""Decoder, query engine, and OAK auditor for the materialized Ω-MAIL-T atlas.

The R0.2 CVCD layout carries semantics across four coordinates:

    layer / company / intent / anomaly / locale

The first three coordinates are encoded by the directory and file path. The
last two coordinates are encoded by one line in the ``*.cells`` file. This
keeps every record addressable and Git-reviewable while allowing Git's content
addressing to deduplicate the repeated anomaly-locale grid.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence


DEFAULT_CVCD_ROOT = Path("generated/omega_mail_t_r02_cvcd")
LAYERS = ("scenario", "routing", "oak")
EXPECTED_COMPANY_COUNT = 16
EXPECTED_INTENT_COUNT = 16
EXPECTED_ANOMALY_COUNT = 16
EXPECTED_LOCALE_COUNT = 4
EXPECTED_CELLS_PER_FILE = EXPECTED_ANOMALY_COUNT * EXPECTED_LOCALE_COUNT
EXPECTED_FILES_PER_LAYER = EXPECTED_COMPANY_COUNT * EXPECTED_INTENT_COUNT
EXPECTED_RECORDS_PER_LAYER = EXPECTED_FILES_PER_LAYER * EXPECTED_CELLS_PER_FILE
EXPECTED_TOTAL_RECORDS = EXPECTED_RECORDS_PER_LAYER * len(LAYERS)


@dataclass(frozen=True, slots=True)
class AtlasCell:
    """One decoded materialized atlas record."""

    record_id: str
    layer: str
    company_code: str
    company: str
    intent_code: str
    intent: str
    anomaly_code: str
    anomaly: str
    locale_code: str
    locale: str
    source_path: str
    source_line: int
    synthetic: bool = True
    external_delivery_allowed: bool = False
    data_classification: str = "synthetic_internal"


@dataclass(frozen=True, slots=True)
class AtlasAudit:
    """Structural and OAK validation result for a CVCD atlas."""

    valid: bool
    total_records: int
    records_by_layer: Mapping[str, int]
    expected_total_records: int
    expected_files: int
    observed_files: int
    unique_content_hashes: int
    missing_files: tuple[str, ...]
    unexpected_files: tuple[str, ...]
    malformed_files: tuple[str, ...]
    unsafe_manifest_flags: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def expected_cell_lines() -> tuple[str, ...]:
    """Return the canonical 64 anomaly-locale cells in stable order."""

    return tuple(
        f"a{anomaly_index:02d}|l{locale_index}"
        for anomaly_index in range(EXPECTED_ANOMALY_COUNT)
        for locale_index in range(EXPECTED_LOCALE_COUNT)
    )


def parse_cell_line(raw: str) -> tuple[str, str]:
    """Parse and validate one compact ``aXX|lY`` cell line."""

    line = raw.strip()
    parts = line.split("|")
    if len(parts) != 2:
        raise ValueError(f"Malformed cell line: {raw!r}")
    anomaly_code, locale_code = parts
    if anomaly_code not in {f"a{index:02d}" for index in range(16)}:
        raise ValueError(f"Unknown anomaly code: {anomaly_code!r}")
    if locale_code not in {f"l{index}" for index in range(4)}:
        raise ValueError(f"Unknown locale code: {locale_code!r}")
    return anomaly_code, locale_code


class CVCDAtlas:
    """Read and audit the materialized intercompany mail test atlas."""

    def __init__(self, root: str | Path = DEFAULT_CVCD_ROOT) -> None:
        self.root = Path(root)
        self._manifest: dict[str, object] | None = None

    @property
    def manifest(self) -> dict[str, object]:
        if self._manifest is None:
            path = self.root / "manifest.json"
            self._manifest = json.loads(path.read_text(encoding="utf-8"))
        return self._manifest

    def _mapping(self, field: str) -> dict[str, str]:
        raw = self.manifest.get(field)
        if not isinstance(raw, dict):
            raise ValueError(f"Manifest field {field!r} must be an object")
        return {str(key): str(value) for key, value in raw.items()}

    @property
    def companies(self) -> dict[str, str]:
        return self._mapping("company_codes")

    @property
    def intents(self) -> dict[str, str]:
        return self._mapping("intent_codes")

    @property
    def anomalies(self) -> dict[str, str]:
        return self._mapping("anomaly_codes")

    @property
    def locales(self) -> dict[str, str]:
        return self._mapping("locale_codes")

    @staticmethod
    def _resolve_codes(
        mapping: Mapping[str, str],
        requested: str | None,
    ) -> tuple[str, ...]:
        if requested is None:
            return tuple(sorted(mapping))
        if requested in mapping:
            return (requested,)
        reverse = {value: key for key, value in mapping.items()}
        if requested in reverse:
            return (reverse[requested],)
        raise KeyError(f"Unknown atlas selector: {requested!r}")

    def expected_paths(self) -> tuple[Path, ...]:
        return tuple(
            self.root / layer / company_code / f"{intent_code}.cells"
            for layer in LAYERS
            for company_code in sorted(self.companies)
            for intent_code in sorted(self.intents)
        )

    def iter_cells(
        self,
        *,
        layer: str | None = None,
        company: str | None = None,
        intent: str | None = None,
        anomaly: str | None = None,
        locale: str | None = None,
        limit: int | None = None,
    ) -> Iterator[AtlasCell]:
        """Stream decoded cells without loading the full atlas into memory."""

        layers: Sequence[str]
        if layer is None:
            layers = LAYERS
        elif layer in LAYERS:
            layers = (layer,)
        else:
            raise KeyError(f"Unknown layer: {layer!r}")

        company_codes = self._resolve_codes(self.companies, company)
        intent_codes = self._resolve_codes(self.intents, intent)
        anomaly_codes = set(self._resolve_codes(self.anomalies, anomaly))
        locale_codes = set(self._resolve_codes(self.locales, locale))

        emitted = 0
        for layer_code in layers:
            for company_code in company_codes:
                for intent_code in intent_codes:
                    path = self.root / layer_code / company_code / f"{intent_code}.cells"
                    with path.open(encoding="utf-8") as handle:
                        for line_number, raw in enumerate(handle, start=1):
                            anomaly_code, locale_code = parse_cell_line(raw)
                            if anomaly_code not in anomaly_codes:
                                continue
                            if locale_code not in locale_codes:
                                continue
                            record_id = ":".join(
                                (
                                    "mail",
                                    layer_code,
                                    company_code,
                                    intent_code,
                                    anomaly_code,
                                    locale_code,
                                )
                            )
                            yield AtlasCell(
                                record_id=record_id,
                                layer=layer_code,
                                company_code=company_code,
                                company=self.companies[company_code],
                                intent_code=intent_code,
                                intent=self.intents[intent_code],
                                anomaly_code=anomaly_code,
                                anomaly=self.anomalies[anomaly_code],
                                locale_code=locale_code,
                                locale=self.locales[locale_code],
                                source_path=path.as_posix(),
                                source_line=line_number,
                            )
                            emitted += 1
                            if limit is not None and emitted >= limit:
                                return

    def audit(self) -> AtlasAudit:
        """Verify cardinality, paths, cell order, hashes, and safety flags."""

        expected_lines = expected_cell_lines()
        expected_paths = self.expected_paths()
        expected_path_strings = {path.as_posix() for path in expected_paths}
        observed_paths = tuple(sorted(self.root.glob("*/*/*.cells")))
        observed_path_strings = {path.as_posix() for path in observed_paths}

        missing_files = tuple(sorted(expected_path_strings - observed_path_strings))
        unexpected_files = tuple(sorted(observed_path_strings - expected_path_strings))
        malformed_files: list[str] = []
        content_hashes: set[str] = set()
        records_by_layer: Counter[str] = Counter()

        for path in observed_paths:
            raw_bytes = path.read_bytes()
            content_hashes.add(hashlib.sha256(raw_bytes).hexdigest())
            lines = tuple(path.read_text(encoding="utf-8").splitlines())
            relative = path.relative_to(self.root)
            layer = relative.parts[0] if relative.parts else "unknown"
            records_by_layer[layer] += len(lines)
            if lines != expected_lines:
                malformed_files.append(path.as_posix())
                continue
            for line in lines:
                parse_cell_line(line)

        unsafe_manifest_flags: list[str] = []
        if self.manifest.get("external_delivery_allowed") is not False:
            unsafe_manifest_flags.append("external_delivery_allowed_must_be_false")
        if self.manifest.get("data_classification") != "synthetic_internal":
            unsafe_manifest_flags.append("data_classification_must_be_synthetic_internal")
        if int(self.manifest.get("total_records", -1)) != EXPECTED_TOTAL_RECORDS:
            unsafe_manifest_flags.append("manifest_total_records_mismatch")
        if int(self.manifest.get("total_files", -1)) != len(expected_paths):
            unsafe_manifest_flags.append("manifest_total_files_mismatch")

        total_records = sum(records_by_layer.values())
        layer_counts_valid = all(
            records_by_layer.get(layer, 0) == EXPECTED_RECORDS_PER_LAYER
            for layer in LAYERS
        )
        valid = (
            total_records == EXPECTED_TOTAL_RECORDS
            and layer_counts_valid
            and len(observed_paths) == len(expected_paths)
            and len(content_hashes) == 1
            and not missing_files
            and not unexpected_files
            and not malformed_files
            and not unsafe_manifest_flags
        )

        return AtlasAudit(
            valid=valid,
            total_records=total_records,
            records_by_layer=dict(sorted(records_by_layer.items())),
            expected_total_records=EXPECTED_TOTAL_RECORDS,
            expected_files=len(expected_paths),
            observed_files=len(observed_paths),
            unique_content_hashes=len(content_hashes),
            missing_files=missing_files,
            unexpected_files=unexpected_files,
            malformed_files=tuple(sorted(malformed_files)),
            unsafe_manifest_flags=tuple(unsafe_manifest_flags),
        )


def _json_dump(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-mail-cvcd")
    parser.add_argument("--root", type=Path, default=DEFAULT_CVCD_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("audit", help="Validate the complete materialized atlas.")
    subparsers.add_parser("stats", help="Print manifest and structural counts.")

    query = subparsers.add_parser("query", help="Stream decoded atlas cells.")
    query.add_argument("--layer", choices=LAYERS)
    query.add_argument("--company")
    query.add_argument("--intent")
    query.add_argument("--anomaly")
    query.add_argument("--locale")
    query.add_argument("--limit", type=int, default=20)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    atlas = CVCDAtlas(args.root)

    if args.command == "audit":
        report = atlas.audit()
        _json_dump(report.to_dict())
        return 0 if report.valid else 1

    if args.command == "stats":
        report = atlas.audit()
        _json_dump(
            {
                "manifest": atlas.manifest,
                "audit": report.to_dict(),
            }
        )
        return 0 if report.valid else 1

    if args.command == "query":
        cells = [
            asdict(cell)
            for cell in atlas.iter_cells(
                layer=args.layer,
                company=args.company,
                intent=args.intent,
                anomaly=args.anomaly,
                locale=args.locale,
                limit=args.limit,
            )
        ]
        _json_dump(cells)
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
