"""Rust/C++ backend source generation for exact sequence kernels.

The generator emits auditable source projects and cross-language fixtures.  It
does not claim that generated code has compiled until an independent build
receipt is attached.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Iterable, Mapping, Sequence

from ..exact import NumberLike, normalize_terms


@dataclass(frozen=True)
class NativeKernelSpec:
    kernel_id: str
    recurrence_coefficients: tuple[Fraction, ...]
    initial_values: tuple[Fraction, ...]
    signed_bits: int = 128
    checked_arithmetic: bool = True

    def __post_init__(self) -> None:
        if not self.kernel_id or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.kernel_id):
            raise ValueError("kernel_id must be a native identifier")
        if not self.recurrence_coefficients:
            raise ValueError("recurrence coefficients are required")
        if len(self.initial_values) < len(self.recurrence_coefficients):
            raise ValueError("initial values must cover recurrence order")
        if self.signed_bits not in {32, 64, 128}:
            raise ValueError("signed_bits must be 32, 64 or 128")

    @classmethod
    def create(
        cls,
        kernel_id: str,
        recurrence_coefficients: Iterable[NumberLike],
        initial_values: Iterable[NumberLike],
        *,
        signed_bits: int = 128,
        checked_arithmetic: bool = True,
    ) -> "NativeKernelSpec":
        return cls(
            kernel_id,
            normalize_terms(recurrence_coefficients),
            normalize_terms(initial_values),
            signed_bits,
            checked_arithmetic,
        )

    @property
    def order(self) -> int:
        return len(self.recurrence_coefficients)

    @property
    def integral(self) -> bool:
        return all(value.denominator == 1 for value in self.recurrence_coefficients + self.initial_values)

    def to_dict(self) -> dict[str, object]:
        return {
            "kernel_id": self.kernel_id,
            "recurrence_coefficients": [str(value) for value in self.recurrence_coefficients],
            "initial_values": [str(value) for value in self.initial_values],
            "order": self.order,
            "signed_bits": self.signed_bits,
            "checked_arithmetic": self.checked_arithmetic,
            "integral": self.integral,
        }

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GeneratedProject:
    language: str
    project_name: str
    files: Mapping[str, str]
    spec_digest: str
    build_command: str
    test_command: str
    compilation_verified: bool = False

    def __post_init__(self) -> None:
        if self.compilation_verified:
            raise ValueError("source generation alone cannot verify compilation")

    def manifest(self) -> dict[str, object]:
        file_digests = {
            path: sha256(content.encode("utf-8")).hexdigest()
            for path, content in sorted(self.files.items())
        }
        payload = {
            "schema": "omega-generated-native-project/1",
            "language": self.language,
            "project_name": self.project_name,
            "spec_digest": self.spec_digest,
            "files": file_digests,
            "build_command": self.build_command,
            "test_command": self.test_command,
            "compilation_verified": False,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload["manifest_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload

    def write(self, directory: str | Path) -> dict[str, object]:
        root = Path(directory)
        for relative, content in self.files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        manifest = self.manifest()
        (root / "omega_codegen_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest


def _require_integral(spec: NativeKernelSpec) -> None:
    if not spec.integral:
        raise ValueError(
            "integer native kernel requires integral coefficients and seeds; "
            "use the future rational backend for fractional recurrences"
        )


def _rust_integer_type(bits: int) -> str:
    return {32: "i32", 64: "i64", 128: "i128"}[bits]


def generate_rust_project(spec: NativeKernelSpec) -> GeneratedProject:
    _require_integral(spec)
    integer = _rust_integer_type(spec.signed_bits)
    coefficients = ", ".join(str(value.numerator) for value in spec.recurrence_coefficients)
    seeds = ", ".join(str(value.numerator) for value in spec.initial_values[: spec.order])
    multiply = "checked_mul" if spec.checked_arithmetic else "wrapping_mul"
    add = "checked_add" if spec.checked_arithmetic else "wrapping_add"
    if spec.checked_arithmetic:
        accumulation = f"""let product = COEFFICIENTS[lag - 1].{multiply}(values[n - lag])
                .ok_or(KernelError::Overflow {{ index: n, lag }})?;
            next = next.{add}(product)
                .ok_or(KernelError::Overflow {{ index: n, lag }})?;"""
    else:
        accumulation = f"""let product = COEFFICIENTS[lag - 1].{multiply}(values[n - lag]);
            next = next.{add}(product);"""
    lib = f"""//! Generated by Ω-SUITE-FORM-T∞ R∞.
//! Source generation is not a compilation or mathematical-proof receipt.

pub type Integer = {integer};
pub const ORDER: usize = {spec.order};
pub const COEFFICIENTS: [Integer; ORDER] = [{coefficients}];
pub const INITIAL: [Integer; ORDER] = [{seeds}];
pub const SPEC_DIGEST: &str = \"{spec.digest()}\";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum KernelError {{
    Overflow {{ index: usize, lag: usize }},
}}

pub fn generate(count: usize) -> Result<Vec<Integer>, KernelError> {{
    let mut values = Vec::with_capacity(count.max(ORDER));
    values.extend(INITIAL.iter().copied().take(count));
    while values.len() < count {{
        let n = values.len();
        let mut next: Integer = 0;
        for lag in 1..=ORDER {{
            {accumulation}
        }}
        values.push(next);
    }}
    Ok(values)
}}

pub fn value(index: usize) -> Result<Integer, KernelError> {{
    Ok(generate(index + 1)?[index])
}}

pub fn verify_prefix(expected: &[Integer]) -> Result<bool, KernelError> {{
    Ok(generate(expected.len())? == expected)
}}

#[cfg(test)]
mod tests {{
    use super::*;

    #[test]
    fn initial_values_roundtrip() {{
        assert_eq!(generate(ORDER).unwrap(), INITIAL.to_vec());
    }}

    #[test]
    fn deterministic_repetition() {{
        assert_eq!(generate(128), generate(128));
    }}

    #[test]
    fn spec_digest_is_sha256_length() {{
        assert_eq!(SPEC_DIGEST.len(), 64);
    }}
}}
"""
    cargo = f"""[package]
name = \"omega-{spec.kernel_id.replace('_', '-')}\"
version = \"0.1.0\"
edition = \"2021\"
publish = false

[lib]
path = \"src/lib.rs\"

[profile.release]
overflow-checks = {str(spec.checked_arithmetic).lower()}
lto = true
codegen-units = 1
"""
    readme = f"""# Generated Rust kernel `{spec.kernel_id}`

- order: {spec.order}
- integer type: `{integer}`
- checked arithmetic: `{spec.checked_arithmetic}`
- spec digest: `{spec.digest()}`

This project is generated research software. Run `cargo test` and preserve the
resulting build receipt before treating it as a validated backend. Finite
prefix agreement does not prove a global mathematical identity.
"""
    return GeneratedProject(
        language="rust",
        project_name=f"omega-{spec.kernel_id}",
        files={"Cargo.toml": cargo, "src/lib.rs": lib, "README.md": readme},
        spec_digest=spec.digest(),
        build_command="cargo build --release --locked",
        test_command="cargo test --all-targets --locked",
    )


def _cpp_integer_type(bits: int) -> str:
    if bits == 32:
        return "std::int32_t"
    if bits == 64:
        return "std::int64_t"
    return "__int128_t"


def generate_cpp_project(spec: NativeKernelSpec) -> GeneratedProject:
    _require_integral(spec)
    integer = _cpp_integer_type(spec.signed_bits)
    coefficients = ", ".join(str(value.numerator) for value in spec.recurrence_coefficients)
    seeds = ", ".join(str(value.numerator) for value in spec.initial_values[: spec.order])
    if spec.checked_arithmetic:
        if spec.signed_bits < 128:
            wide = "std::int64_t" if spec.signed_bits == 32 else "__int128_t"
            arithmetic = f"""const {wide} product = static_cast<{wide}>(kCoefficients[lag - 1]) * values[n - lag];
            const {wide} candidate = static_cast<{wide}>(next) + product;
            if (candidate < std::numeric_limits<Integer>::min() || candidate > std::numeric_limits<Integer>::max()) {{
                return std::nullopt;
            }}
            next = static_cast<Integer>(candidate);"""
        else:
            arithmetic = """Integer product;
            if (__builtin_mul_overflow(kCoefficients[lag - 1], values[n - lag], &product)) return std::nullopt;
            if (__builtin_add_overflow(next, product, &next)) return std::nullopt;"""
    else:
        arithmetic = "next += kCoefficients[lag - 1] * values[n - lag];"
    header = f"""#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <vector>

namespace omega::{spec.kernel_id} {{
using Integer = {integer};
inline constexpr std::size_t kOrder = {spec.order};
inline constexpr std::array<Integer, kOrder> kCoefficients{{{coefficients}}};
inline constexpr std::array<Integer, kOrder> kInitial{{{seeds}}};
inline constexpr const char* kSpecDigest = \"{spec.digest()}\";

inline std::optional<std::vector<Integer>> generate(std::size_t count) {{
    std::vector<Integer> values;
    values.reserve(count > kOrder ? count : kOrder);
    for (std::size_t i = 0; i < count && i < kOrder; ++i) values.push_back(kInitial[i]);
    while (values.size() < count) {{
        const std::size_t n = values.size();
        Integer next = 0;
        for (std::size_t lag = 1; lag <= kOrder; ++lag) {{
            {arithmetic}
        }}
        values.push_back(next);
    }}
    return values;
}}
}}  // namespace omega::{spec.kernel_id}
"""
    test = f"""#include \"omega_kernel.hpp\"
#include <cassert>
#include <cstring>

int main() {{
    using namespace omega::{spec.kernel_id};
    const auto first = generate(128);
    const auto second = generate(128);
    assert(first.has_value());
    assert(second.has_value());
    assert(first == second);
    assert(std::strlen(kSpecDigest) == 64);
    for (std::size_t i = 0; i < kOrder; ++i) assert((*first)[i] == kInitial[i]);
    return 0;
}}
"""
    cmake = f"""cmake_minimum_required(VERSION 3.20)
project(omega_{spec.kernel_id} LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_executable(omega_kernel_test tests/test_kernel.cpp)
target_include_directories(omega_kernel_test PRIVATE include)
if (MSVC)
  target_compile_options(omega_kernel_test PRIVATE /W4 /WX)
else()
  target_compile_options(omega_kernel_test PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
enable_testing()
add_test(NAME omega_kernel_test COMMAND omega_kernel_test)
"""
    readme = f"""# Generated C++ kernel `{spec.kernel_id}`

The source uses `{integer}` and checked arithmetic is `{spec.checked_arithmetic}`.
The project has not been compiled by the generator. Build and test receipts are
required before backend certification.
"""
    return GeneratedProject(
        language="cpp",
        project_name=f"omega-{spec.kernel_id}",
        files={
            "CMakeLists.txt": cmake,
            "include/omega_kernel.hpp": header,
            "tests/test_kernel.cpp": test,
            "README.md": readme,
        },
        spec_digest=spec.digest(),
        build_command="cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --config Release",
        test_command="ctest --test-dir build --output-on-failure",
    )


def cross_language_fixture(
    spec: NativeKernelSpec,
    *,
    expected_terms: Iterable[NumberLike],
) -> dict[str, object]:
    terms = normalize_terms(expected_terms)
    payload = {
        "schema": "omega-native-cross-language-fixture/1",
        "kernel": spec.to_dict(),
        "kernel_digest": spec.digest(),
        "expected_terms": [str(value) for value in terms],
        "expected_terms_digest": sha256(
            json.dumps([str(value) for value in terms], separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "required_backends": ["python", "rust", "cpp"],
        "required_checks": [
            "exact_term_agreement",
            "deterministic_repetition",
            "overflow_behavior",
            "input_digest_agreement",
            "output_digest_agreement",
        ],
        "backend_validation_completed": False,
        "global_identity_proved": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["fixture_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def project_bundle(spec: NativeKernelSpec) -> dict[str, GeneratedProject]:
    return {
        "rust": generate_rust_project(spec),
        "cpp": generate_cpp_project(spec),
    }
