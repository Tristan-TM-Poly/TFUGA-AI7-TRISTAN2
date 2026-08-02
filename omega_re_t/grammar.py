"""Conservative grammar inference for synthetic or authorized record formats."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from json import dumps
from re import fullmatch
from typing import Iterable, Sequence


class FieldKind(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    HEX = "hex"
    BOOLEAN = "boolean"
    ENUM = "enum"
    TEXT = "text"
    EMPTY = "empty"


@dataclass(frozen=True, slots=True)
class FieldSpec:
    index: int
    name: str
    kind: FieldKind
    optional: bool
    observed_values: tuple[str, ...]
    enum_values: tuple[str, ...] = ()
    minimum_length: int = 0
    maximum_length: int = 0

    def accepts(self, value: str) -> bool:
        if value == "" and self.optional:
            return True
        if self.kind is FieldKind.INTEGER:
            return fullmatch(r"[+-]?\d+", value) is not None
        if self.kind is FieldKind.FLOAT:
            return fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value) is not None
        if self.kind is FieldKind.HEX:
            return fullmatch(r"(?:0x)?[0-9A-Fa-f]+", value) is not None
        if self.kind is FieldKind.BOOLEAN:
            return value.lower() in {"true", "false", "0", "1", "yes", "no"}
        if self.kind is FieldKind.ENUM:
            return value in self.enum_values
        if self.kind is FieldKind.EMPTY:
            return value == ""
        return self.minimum_length <= len(value) <= self.maximum_length


@dataclass(frozen=True, slots=True)
class DelimitedGrammar:
    delimiter: str
    fields: tuple[FieldSpec, ...]
    record_count: int
    strict_field_count: bool = True

    def parse(self, record: str) -> dict[str, str]:
        parts = record.rstrip("\n").split(self.delimiter)
        if self.strict_field_count and len(parts) != len(self.fields):
            raise ValueError(f"Expected {len(self.fields)} fields, got {len(parts)}")
        if len(parts) > len(self.fields):
            raise ValueError("record contains unknown trailing fields")
        result: dict[str, str] = {}
        for spec in self.fields:
            value = parts[spec.index] if spec.index < len(parts) else ""
            if not spec.accepts(value):
                raise ValueError(f"Field {spec.name!r} rejects value {value!r}")
            result[spec.name] = value
        return result

    def digest(self) -> str:
        payload = {
            "delimiter": self.delimiter,
            "record_count": self.record_count,
            "strict_field_count": self.strict_field_count,
            "fields": [
                {
                    "index": f.index,
                    "name": f.name,
                    "kind": f.kind.value,
                    "optional": f.optional,
                    "observed_values": f.observed_values,
                    "enum_values": f.enum_values,
                    "minimum_length": f.minimum_length,
                    "maximum_length": f.maximum_length,
                }
                for f in self.fields
            ],
        }
        return sha256(dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class GrammarInferenceReport:
    grammar: DelimitedGrammar
    candidate_delimiters: tuple[tuple[str, float], ...]
    rejected_records: tuple[str, ...]
    ambiguities: tuple[str, ...]


def _classify(values: Sequence[str], enum_limit: int) -> tuple[FieldKind, tuple[str, ...]]:
    nonempty = [value for value in values if value != ""]
    if not nonempty:
        return FieldKind.EMPTY, ()
    if all(fullmatch(r"[+-]?\d+", value) for value in nonempty):
        return FieldKind.INTEGER, ()
    if all(fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value) for value in nonempty):
        return FieldKind.FLOAT, ()
    if all(fullmatch(r"(?:0x)?[0-9A-Fa-f]+", value) for value in nonempty) and any(any(c in "ABCDEFabcdef" for c in value) for value in nonempty):
        return FieldKind.HEX, ()
    if all(value.lower() in {"true", "false", "0", "1", "yes", "no"} for value in nonempty):
        return FieldKind.BOOLEAN, ()
    unique = tuple(sorted(set(nonempty)))
    if len(unique) <= enum_limit and len(unique) < max(3, len(nonempty) // 2 + 1):
        return FieldKind.ENUM, unique
    return FieldKind.TEXT, ()


def delimiter_scores(records: Sequence[str], candidates: Sequence[str]) -> tuple[tuple[str, float], ...]:
    scores: list[tuple[str, float]] = []
    for delimiter in candidates:
        counts = [len(record.rstrip("\n").split(delimiter)) for record in records]
        if not counts:
            score = 0.0
        else:
            mode = max(set(counts), key=counts.count)
            consistency = counts.count(mode) / len(counts)
            score = consistency * (1.0 if mode > 1 else 0.0)
        scores.append((delimiter, score))
    return tuple(sorted(scores, key=lambda item: (-item[1], item[0])))


def infer_delimited_grammar(
    records: Iterable[str],
    *,
    candidate_delimiters: Sequence[str] = (",", "|", ";", "\t", ":"),
    field_names: Sequence[str] | None = None,
    enum_limit: int = 12,
) -> GrammarInferenceReport:
    rows = tuple(record.rstrip("\n") for record in records)
    if not rows:
        raise ValueError("at least one record is required")
    scores = delimiter_scores(rows, candidate_delimiters)
    delimiter, score = scores[0]
    if score <= 0.0:
        raise ValueError("no consistent delimiter was inferred")
    split_rows = [row.split(delimiter) for row in rows]
    field_count = max(set(map(len, split_rows)), key=lambda count: sum(len(row) == count for row in split_rows))
    accepted = [row for row in split_rows if len(row) == field_count]
    rejected = tuple(rows[index] for index, row in enumerate(split_rows) if len(row) != field_count)
    if field_names is not None and len(field_names) != field_count:
        raise ValueError("field_names length does not match inferred field count")
    names = tuple(field_names) if field_names is not None else tuple(f"field_{index}" for index in range(field_count))
    specs: list[FieldSpec] = []
    ambiguities: list[str] = []
    for index in range(field_count):
        values = [row[index] for row in accepted]
        kind, enum_values = _classify(values, enum_limit)
        optional = any(value == "" for value in values)
        lengths = [len(value) for value in values]
        if kind is FieldKind.TEXT and len(set(values)) <= enum_limit:
            ambiguities.append(f"{names[index]} may be text or an under-sampled enumeration")
        specs.append(
            FieldSpec(
                index=index,
                name=names[index],
                kind=kind,
                optional=optional,
                observed_values=tuple(sorted(set(values))),
                enum_values=enum_values,
                minimum_length=min(lengths),
                maximum_length=max(lengths),
            )
        )
    grammar = DelimitedGrammar(delimiter, tuple(specs), len(accepted), strict_field_count=True)
    return GrammarInferenceReport(grammar, scores, rejected, tuple(ambiguities))
