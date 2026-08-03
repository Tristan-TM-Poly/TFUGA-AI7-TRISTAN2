from __future__ import annotations

from collections.abc import Sequence

from ..ntt import build_ntt_profile


def _require_power_of_two(length: int) -> None:
    if length < 1 or length & (length - 1):
        raise ValueError("length must be a positive power of two")


def _bit_reverse_permute(values: list[int]) -> None:
    n = len(values)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            values[i], values[j] = values[j], values[i]


def ntt(values: Sequence[int], modulus: int, *, inverse: bool = False) -> list[int]:
    """Iterative radix-2 NTT over a proven machine-size prime modulus."""
    n = len(values)
    _require_power_of_two(n)
    profile = build_ntt_profile(modulus)
    if n > profile.maximum_transform_length:
        raise ValueError("transform length exceeds modulus two-adicity")
    data = [int(value) % modulus for value in values]
    _bit_reverse_permute(data)
    length = 2
    while length <= n:
        stage_root = pow(profile.primitive_root, (modulus - 1) // length, modulus)
        if inverse:
            stage_root = pow(stage_root, modulus - 2, modulus)
        half = length // 2
        for offset in range(0, n, length):
            omega = 1
            for index in range(offset, offset + half):
                even = data[index]
                odd = data[index + half] * omega % modulus
                data[index] = (even + odd) % modulus
                data[index + half] = (even - odd) % modulus
                omega = omega * stage_root % modulus
        length <<= 1
    if inverse:
        inverse_n = pow(n, modulus - 2, modulus)
        data = [value * inverse_n % modulus for value in data]
    return data


def convolution(left: Sequence[int], right: Sequence[int], modulus: int) -> list[int]:
    if not left or not right:
        return []
    output_length = len(left) + len(right) - 1
    size = 1
    while size < output_length:
        size <<= 1
    padded_left = list(left) + [0] * (size - len(left))
    padded_right = list(right) + [0] * (size - len(right))
    spectrum_left = ntt(padded_left, modulus)
    spectrum_right = ntt(padded_right, modulus)
    product = [(a * b) % modulus for a, b in zip(spectrum_left, spectrum_right, strict=True)]
    return ntt(product, modulus, inverse=True)[:output_length]


def naive_convolution(left: Sequence[int], right: Sequence[int], modulus: int) -> list[int]:
    if not left or not right:
        return []
    result = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] = (result[i + j] + a * b) % modulus
    return result


def validate_convolution(left: Sequence[int], right: Sequence[int], modulus: int) -> dict[str, object]:
    fast = convolution(left, right, modulus)
    reference = naive_convolution(left, right, modulus)
    return {
        "modulus": modulus,
        "left_length": len(left),
        "right_length": len(right),
        "output_length": len(fast),
        "matches_naive": fast == reference,
        "result": fast,
    }
