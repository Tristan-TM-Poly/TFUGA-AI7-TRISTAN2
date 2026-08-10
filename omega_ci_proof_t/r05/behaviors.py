from __future__ import annotations

from typing import Callable


def normalize_exact_prefix(value: str) -> str:
    return value[2:] if value.startswith("./") else value


def normalize_lstrip_charset(value: str) -> str:
    return value.lstrip("./")


def normalize_strip_charset(value: str) -> str:
    return value.strip("./")


def normalize_remove_leading_dot(value: str) -> str:
    return value[1:] if value.startswith(".") else value


def normalize_identity(value: str) -> str:
    return value


def normalize_all_relative_prefixes(value: str) -> str:
    while value.startswith("./"):
        value = value[2:]
    return value


def normalize_exact_prefix_clone(value: str) -> str:
    if value[:2] == "./":
        return value[2:]
    return value


BEHAVIORS: dict[str, Callable[[str], str]] = {
    "exact_prefix": normalize_exact_prefix,
    "lstrip_charset": normalize_lstrip_charset,
    "strip_charset": normalize_strip_charset,
    "remove_leading_dot": normalize_remove_leading_dot,
    "identity": normalize_identity,
    "all_relative_prefixes": normalize_all_relative_prefixes,
    "exact_prefix_clone": normalize_exact_prefix_clone,
}


def resolve_behavior(name: str) -> Callable[[str], str]:
    try:
        return BEHAVIORS[name]
    except KeyError as exc:
        raise KeyError(f"unknown behavior: {name}") from exc
