from __future__ import annotations

from dataclasses import dataclass

EUROSTAT_UNIT_MAP = {"KG_HAB": "kg_per_capita", "THS_T": "thousand_tonnes", "T": "tonnes"}


@dataclass(frozen=True, slots=True)
class EurostatObservation:
    dimensions: tuple[tuple[str, str], ...]
    period: str
    value: float | None
    status: str | None = None

    def dimension(self, name: str) -> str:
        for key, value in self.dimensions:
            if key == name:
                return value
        raise KeyError(name)

    @property
    def unit_code(self) -> str:
        return self.dimension("unit")

    @property
    def normalized_unit(self) -> str:
        return EUROSTAT_UNIT_MAP.get(self.unit_code, self.unit_code)


@dataclass(frozen=True, slots=True)
class EnvWasmunObservation:
    geo: str
    period: str
    waste_operation: str
    unit_code: str
    normalized_unit: str
    value: float | None
    status: str | None


def _parse_value_status(cell: str) -> tuple[float | None, str | None]:
    token = cell.strip()
    if not token:
        return None, None
    parts = token.split()
    if parts[0] == ":":
        return None, " ".join(parts[1:]) or None
    try:
        value = float(parts[0])
    except ValueError as exc:
        raise ValueError(f"invalid Eurostat numeric cell: {cell!r}") from exc
    return value, " ".join(parts[1:]) or None


def parse_eurostat_tsv(text: str) -> tuple[EurostatObservation, ...]:
    """Parse Eurostat TSV while preserving raw dimension codes and status flags."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("Eurostat TSV requires a header and at least one data row")
    header = lines[0].split("\t")
    first = header[0].strip()
    for marker in ("\\TIME_PERIOD", "\\time", "\\TIME"):
        first = first.replace(marker, "")
    dimensions = tuple(part.strip() for part in first.split(",") if part.strip())
    if not dimensions:
        raise ValueError("Eurostat TSV dimension header is empty")
    periods = tuple(cell.strip() for cell in header[1:])
    if not periods or any(not period for period in periods):
        raise ValueError("Eurostat TSV requires non-empty time-period columns")

    result: list[EurostatObservation] = []
    for line in lines[1:]:
        cells = line.split("\t")
        keys = tuple(part.strip() for part in cells[0].split(","))
        if len(keys) != len(dimensions):
            raise ValueError("Eurostat series key does not match dimension header")
        dim_pairs = tuple(zip(dimensions, keys))
        data_cells = list(cells[1:])
        if len(data_cells) < len(periods):
            data_cells.extend([""] * (len(periods) - len(data_cells)))
        if len(data_cells) > len(periods):
            raise ValueError("Eurostat row has more values than time-period columns")
        for period, cell in zip(periods, data_cells):
            value, status = _parse_value_status(cell)
            result.append(EurostatObservation(dim_pairs, period, value, status))
    return tuple(result)


def adapt_env_wasmun_tsv(text: str) -> tuple[EnvWasmunObservation, ...]:
    observations = parse_eurostat_tsv(text)
    if not observations:
        return ()
    dimensions = {key for key, _ in observations[0].dimensions}
    missing = {"geo", "unit", "wst_oper"} - dimensions
    if missing:
        raise ValueError(f"env_wasmun TSV missing required dimensions: {sorted(missing)}")
    return tuple(
        EnvWasmunObservation(
            geo=obs.dimension("geo"),
            period=obs.period,
            waste_operation=obs.dimension("wst_oper"),
            unit_code=obs.unit_code,
            normalized_unit=obs.normalized_unit,
            value=obs.value,
            status=obs.status,
        )
        for obs in observations
    )
