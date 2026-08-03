"""Block partitions, block orbits and exact stitching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .linalg import Matrix, block_extract, block_insert, frobenius_norm, shape, subtract, zeros


@dataclass(frozen=True)
class BlockSpec:
    block_id: str
    row_start: int
    row_stop: int
    col_start: int
    col_stop: int
    orbit: str | None = None

    @property
    def shape(self) -> tuple[int, int]:
        return self.row_stop - self.row_start, self.col_stop - self.col_start

    @property
    def dimension(self) -> int:
        rows, cols = self.shape
        return rows * cols


@dataclass(frozen=True)
class BlockRecord:
    spec: BlockSpec
    values: Matrix
    norm: float


class BlockPartition:
    def __init__(self, matrix_shape: tuple[int, int], specs: Iterable[BlockSpec]):
        self.matrix_shape = matrix_shape
        self.specs = tuple(specs)
        if not self.specs:
            raise ValueError("partition requires at least one block")
        self._validate()

    @classmethod
    def regular(
        cls,
        rows: int,
        cols: int,
        row_splits: Sequence[int],
        col_splits: Sequence[int],
    ) -> "BlockPartition":
        row_bounds = (0,) + tuple(row_splits) + (rows,)
        col_bounds = (0,) + tuple(col_splits) + (cols,)
        if tuple(sorted(set(row_bounds))) != row_bounds or tuple(sorted(set(col_bounds))) != col_bounds:
            raise ValueError("splits must be strictly increasing and inside bounds")
        specs = []
        for row_index, (row_start, row_stop) in enumerate(
            zip(row_bounds[:-1], row_bounds[1:], strict=True)
        ):
            for col_index, (col_start, col_stop) in enumerate(
                zip(col_bounds[:-1], col_bounds[1:], strict=True)
            ):
                specs.append(
                    BlockSpec(
                        block_id=f"b{row_index}_{col_index}",
                        row_start=row_start,
                        row_stop=row_stop,
                        col_start=col_start,
                        col_stop=col_stop,
                    )
                )
        return cls((rows, cols), specs)

    def _validate(self) -> None:
        rows, cols = self.matrix_shape
        occupancy = [[0 for _ in range(cols)] for _ in range(rows)]
        ids = set()
        for spec in self.specs:
            if spec.block_id in ids:
                raise ValueError("block IDs must be unique")
            ids.add(spec.block_id)
            if not (
                0 <= spec.row_start < spec.row_stop <= rows
                and 0 <= spec.col_start < spec.col_stop <= cols
            ):
                raise ValueError(f"invalid bounds for block {spec.block_id}")
            for row in range(spec.row_start, spec.row_stop):
                for col in range(spec.col_start, spec.col_stop):
                    occupancy[row][col] += 1
        if any(value != 1 for row in occupancy for value in row):
            raise ValueError("blocks must form a disjoint complete partition")

    def analyze(self, matrix: Matrix) -> tuple[BlockRecord, ...]:
        if shape(matrix) != self.matrix_shape:
            raise ValueError("matrix shape does not match partition")
        records = []
        for spec in self.specs:
            values = block_extract(
                matrix,
                spec.row_start,
                spec.row_stop,
                spec.col_start,
                spec.col_stop,
            )
            records.append(BlockRecord(spec, values, frobenius_norm(values)))
        return tuple(records)

    def synthesize(self, records: Iterable[BlockRecord]) -> Matrix:
        result = zeros(*self.matrix_shape)
        records_by_id = {record.spec.block_id: record for record in records}
        for spec in self.specs:
            if spec.block_id not in records_by_id:
                raise ValueError(f"missing block {spec.block_id}")
            result = block_insert(
                result,
                records_by_id[spec.block_id].values,
                spec.row_start,
                spec.col_start,
            )
        return result

    def audit(self, matrix: Matrix) -> dict[str, float | int | bool]:
        records = self.analyze(matrix)
        reconstruction = self.synthesize(records)
        residual = subtract(matrix, reconstruction)
        return {
            "block_count": len(records),
            "covered_dimension": sum(record.spec.dimension for record in records),
            "ambient_dimension": self.matrix_shape[0] * self.matrix_shape[1],
            "reconstruction_error": frobenius_norm(residual),
            "exact": frobenius_norm(residual) <= 1e-12,
        }


def orbit_summary(records: Iterable[BlockRecord]) -> dict[str, dict[str, float | int]]:
    groups: dict[str, list[BlockRecord]] = {}
    for record in records:
        orbit = record.spec.orbit or record.spec.block_id
        groups.setdefault(orbit, []).append(record)
    return {
        orbit: {
            "block_count": len(group),
            "total_dimension": sum(record.spec.dimension for record in group),
            "total_energy": sum(record.norm * record.norm for record in group),
        }
        for orbit, group in sorted(groups.items())
    }
