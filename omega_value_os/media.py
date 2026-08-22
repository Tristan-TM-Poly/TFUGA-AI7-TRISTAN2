"""Provider-neutral media/content graph primitives.

The compiler creates candidate projections with provenance. It does not post to
external platforms and does not fabricate source claims.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

EPSILON = 1e-9


@dataclass(frozen=True)
class ContentAsset:
    asset_id: str
    title: str
    source_refs: Tuple[str, ...]
    evidence_refs: Tuple[str, ...] = ()
    rights: Tuple[str, ...] = ()
    version: int = 1


@dataclass(frozen=True)
class ChannelProfile:
    name: str
    audience_fit: float
    trust_gain: float
    conversion_signal: float
    asset_value: float
    production_cost: float
    platform_dependency: float
    policy_risk: float


@dataclass(frozen=True)
class ContentProjection:
    source_asset_id: str
    channel: str
    format: str
    language: str
    source_version: int
    requires_review: bool = True


def channel_score(profile: ChannelProfile) -> float:
    numerator = max(0.0, profile.audience_fit)
    numerator *= max(0.0, profile.trust_gain)
    numerator *= max(0.0, profile.conversion_signal)
    numerator *= max(0.0, profile.asset_value)
    denominator = (
        max(0.0, profile.production_cost)
        + max(0.0, profile.platform_dependency)
        + max(0.0, profile.policy_risk)
    )
    return numerator / max(EPSILON, denominator)


def route_channels(profiles: Iterable[ChannelProfile]) -> Tuple[ChannelProfile, ...]:
    """Rank candidates; ranking is not permission to publish."""
    return tuple(sorted(profiles, key=channel_score, reverse=True))


def compile_projections(
    asset: ContentAsset,
    channels: Iterable[str],
    formats: Iterable[str],
    languages: Iterable[str],
) -> Tuple[ContentProjection, ...]:
    if not asset.source_refs:
        raise ValueError("a derived media asset requires at least one source reference")

    projections = []
    for channel in channels:
        for output_format in formats:
            for language in languages:
                projections.append(
                    ContentProjection(
                        source_asset_id=asset.asset_id,
                        channel=channel,
                        format=output_format,
                        language=language,
                        source_version=asset.version,
                        requires_review=True,
                    )
                )
    return tuple(projections)
