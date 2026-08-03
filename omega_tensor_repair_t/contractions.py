"""Programmable dense tensor contractions with explicit receipts.

Contractions are represented as sequential axis-pair operations. Each step acts
on the current tensor state, so a plan is deterministic and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import prod, sqrt
from typing import Iterable, Sequence

from .higher_order import DenseTensor


def _strides(shape: Sequence[int]) -> tuple[int, ...]:
    result: list[int] = []
    running = 1
    for size in reversed(shape):
        result.append(running)
        running *= size
    return tuple(reversed(result))


def _flat_index(index: Sequence[int], shape: Sequence[int]) -> int:
    if len(index) != len(shape):
        raise ValueError("index rank must match shape")
    strides = _strides(shape)
    offset = 0
    for coordinate, size, stride in zip(index, shape, strides, strict=True):
        if coordinate < 0 or coordinate >= size:
            raise IndexError(tuple(index))
        offset += coordinate * stride
    return offset


@dataclass(frozen=True)
class TensorState:
    """Dense tensor state that also permits rank-zero scalars."""

    shape: tuple[int, ...]
    data: tuple[float, ...]

    def __post_init__(self) -> None:
        expected = prod(self.shape) if self.shape else 1
        if any(size <= 0 for size in self.shape):
            raise ValueError("shape dimensions must be positive")
        if len(self.data) != expected:
            raise ValueError("data length does not match shape")

    @classmethod
    def from_dense(cls, tensor: DenseTensor) -> "TensorState":
        return cls(tensor.shape, tensor.data)

    @property
    def rank(self) -> int:
        return len(self.shape)

    @property
    def dimension(self) -> int:
        return len(self.data)

    @property
    def scalar(self) -> float:
        if self.shape:
            raise ValueError("state is not scalar")
        return self.data[0]

    def at(self, index: Sequence[int]) -> float:
        if not self.shape:
            if tuple(index):
                raise IndexError(tuple(index))
            return self.scalar
        return self.data[_flat_index(index, self.shape)]

    def norm(self) -> float:
        return sqrt(sum(value * value for value in self.data))

    def to_dense(self) -> DenseTensor:
        if not self.shape:
            raise ValueError("rank-zero state cannot be converted to DenseTensor")
        return DenseTensor(self.shape, self.data)

    def to_dict(self) -> dict[str, object]:
        return {
            "shape": list(self.shape),
            "rank": self.rank,
            "dimension": self.dimension,
            "data": list(self.data),
            "norm": self.norm(),
        }


@dataclass(frozen=True)
class ContractionStep:
    left_axis: int
    right_axis: int
    label: str = "trace"

    def __post_init__(self) -> None:
        if self.left_axis == self.right_axis:
            raise ValueError("contraction axes must be distinct")
        if self.left_axis < 0 or self.right_axis < 0:
            raise ValueError("contraction axes must be non-negative")


@dataclass(frozen=True)
class ContractionReceipt:
    input_shape: tuple[int, ...]
    output_shape: tuple[int, ...]
    step: ContractionStep
    summed_dimension: int
    input_norm: float
    output_norm: float

    def to_dict(self) -> dict[str, object]:
        return {
            "input_shape": list(self.input_shape),
            "output_shape": list(self.output_shape),
            "step": {
                "left_axis": self.step.left_axis,
                "right_axis": self.step.right_axis,
                "label": self.step.label,
            },
            "summed_dimension": self.summed_dimension,
            "input_norm": self.input_norm,
            "output_norm": self.output_norm,
        }


@dataclass(frozen=True)
class ContractionPlanResult:
    output: TensorState
    receipts: tuple[ContractionReceipt, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "output": self.output.to_dict(),
            "receipts": [receipt.to_dict() for receipt in self.receipts],
        }


def contract_pair(
    state: TensorState | DenseTensor,
    left_axis: int,
    right_axis: int,
    *,
    label: str = "trace",
) -> tuple[TensorState, ContractionReceipt]:
    current = TensorState.from_dense(state) if isinstance(state, DenseTensor) else state
    step = ContractionStep(left_axis, right_axis, label)
    if current.rank < 2:
        raise ValueError("pair contraction requires rank at least two")
    if left_axis >= current.rank or right_axis >= current.rank:
        raise ValueError("contraction axis outside current rank")
    if current.shape[left_axis] != current.shape[right_axis]:
        raise ValueError("contracted axes must have equal dimensions")

    contracted_axes = {left_axis, right_axis}
    output_axes = tuple(axis for axis in range(current.rank) if axis not in contracted_axes)
    output_shape = tuple(current.shape[axis] for axis in output_axes)
    output_indices: Iterable[tuple[int, ...]]
    output_indices = product(*(range(size) for size in output_shape)) if output_shape else [tuple()]
    values: list[float] = []
    summed_dimension = current.shape[left_axis]

    for output_index in output_indices:
        total = 0.0
        for diagonal in range(summed_dimension):
            source = [0 for _ in range(current.rank)]
            source[left_axis] = diagonal
            source[right_axis] = diagonal
            for local_axis, source_axis in enumerate(output_axes):
                source[source_axis] = output_index[local_axis]
            total += current.at(source)
        values.append(total)

    output = TensorState(output_shape, tuple(values))
    receipt = ContractionReceipt(
        input_shape=current.shape,
        output_shape=output_shape,
        step=step,
        summed_dimension=summed_dimension,
        input_norm=current.norm(),
        output_norm=output.norm(),
    )
    return output, receipt


@dataclass(frozen=True)
class ContractionPlan:
    steps: tuple[ContractionStep, ...]
    name: str = "contraction-plan"

    def apply(self, tensor: TensorState | DenseTensor) -> ContractionPlanResult:
        state = TensorState.from_dense(tensor) if isinstance(tensor, DenseTensor) else tensor
        receipts: list[ContractionReceipt] = []
        for step in self.steps:
            state, receipt = contract_pair(
                state,
                step.left_axis,
                step.right_axis,
                label=step.label,
            )
            receipts.append(receipt)
        return ContractionPlanResult(state, tuple(receipts))


def trace_matrix_tensor(tensor: DenseTensor) -> float:
    if tensor.rank != 2 or tensor.shape[0] != tensor.shape[1]:
        raise ValueError("trace_matrix_tensor requires a square rank-2 tensor")
    output, _ = contract_pair(tensor, 0, 1, label="matrix-trace")
    return output.scalar


def double_trace_rank4(tensor: DenseTensor) -> float:
    if tensor.rank != 4 or len(set(tensor.shape)) != 1:
        raise ValueError("double_trace_rank4 requires equal dimensions on four axes")
    plan = ContractionPlan(
        (
            ContractionStep(0, 1, "first-trace"),
            ContractionStep(0, 1, "second-trace"),
        ),
        name="double-trace",
    )
    return plan.apply(tensor).output.scalar
