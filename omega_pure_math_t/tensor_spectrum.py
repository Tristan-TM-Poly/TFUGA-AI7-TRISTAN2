"""Finite symbolic Tensor Spectrum channels.

The module does not alter the standard tensor product. It records explicitly
chosen channels derived from it and their dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TensorChannel:
    name: str
    dimension: int
    construction: str
    canonical_under: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.dimension < 0:
            raise ValueError("channel dimension must be non-negative")


@dataclass(frozen=True)
class TensorSpectrum:
    left_dimension: int
    right_dimension: int
    channels: tuple[TensorChannel, ...]

    @property
    def tensor_product_dimension(self) -> int:
        return self.left_dimension * self.right_dimension

    def dimensions(self) -> tuple[int, ...]:
        return tuple(channel.dimension for channel in self.channels)

    def by_name(self, name: str) -> TensorChannel:
        for channel in self.channels:
            if channel.name == name:
                return channel
        raise KeyError(name)


def second_tensor_power_spectrum(
    dimension: int,
    *,
    include_trace_channel: bool = False,
) -> TensorSpectrum:
    """Standard V⊗V, Sym²(V), Λ²(V) dimension decomposition.

    `trace` is optional because it requires additional structure (e.g. a chosen
    non-degenerate bilinear form); it is not canonical for a bare vector space.
    """

    if dimension < 0:
        raise ValueError("dimension must be non-negative")
    channels = [
        TensorChannel(
            "tensor",
            dimension * dimension,
            "V⊗V",
            "linear isomorphisms of V",
        ),
        TensorChannel(
            "symmetric",
            dimension * (dimension + 1) // 2,
            "Sym²(V)",
            "linear isomorphisms of V",
        ),
        TensorChannel(
            "alternating",
            dimension * (dimension - 1) // 2,
            "Λ²(V)",
            "linear isomorphisms of V",
        ),
    ]
    if include_trace_channel and dimension:
        channels.append(
            TensorChannel(
                "trace",
                1,
                "contraction against a chosen non-degenerate bilinear form",
                "isometries preserving the chosen form",
                "requires extra metric/bilinear structure",
            )
        )
    return TensorSpectrum(dimension, dimension, tuple(channels))


def channel_dimension_conservation(spectrum: TensorSpectrum) -> bool:
    """For the Sym²⊕Λ² split, verify n²=n(n+1)/2+n(n-1)/2."""

    names = {channel.name for channel in spectrum.channels}
    if not {"tensor", "symmetric", "alternating"} <= names:
        return False
    return (
        spectrum.by_name("symmetric").dimension
        + spectrum.by_name("alternating").dimension
        == spectrum.by_name("tensor").dimension
    )


def custom_tensor_spectrum(
    left_dimension: int,
    right_dimension: int,
    channels: Iterable[TensorChannel],
) -> TensorSpectrum:
    if left_dimension < 0 or right_dimension < 0:
        raise ValueError("dimensions must be non-negative")
    return TensorSpectrum(left_dimension, right_dimension, tuple(channels))
