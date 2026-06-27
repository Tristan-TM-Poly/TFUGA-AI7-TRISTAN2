# DeepTech Forge → Company Revenue IP Publication OS Bridge

Status: OAK-safe review packet generator.  
Issue: #89.

## Purpose

Connect `omega_deeptech_forge` signal triage to reviewable business/IP/publication packets without sending anything externally, filing anything, or exposing sensitive invention details.

```text
Signal
-> EvidenceLevel
-> OAKStatus
-> IPClass
-> HandoffPacket
-> ReviewPacket
-> OfferCard / PriorArtQueryPack / PublicationNote / IPDisclosureDraft
-> approval record
```

## New module

```text
omega_deeptech_forge/review_packets.py
```

Main entry point:

```python
from omega_deeptech_forge import build_review_packet
```

## Packet routes

| Route | Output | External action? |
|---|---|---|
| `blocked_repair` | metadata repair packet | no |
| `draft_research_review` | source repair packet | no |
| `ip_review_packet` | redacted prior-art pack + private IP draft | no |
| `service_offer_card` | reviewable service/revenue offer card | no |
| `open_publication_note` | publication-safe note draft | no |
| `negative_memory_archive` | archive/observe packet | no |

## OAK safeguards

- `PATENT_REVIEW` and `TRADE_SECRET` routes inherit redaction from `HandoffPacket`.
- Sensitive summaries and source URLs are withheld from public-safe JSON.
- No packet authorizes outreach, publication, filing, revenue claims, or legal/IP claims.
- Every packet includes M⁻ warnings.
- Offer cards include forbidden actions such as `external_outreach_without_approval` and `ip_disclosure_without_review`.

## Minimal example

```python
from omega_deeptech_forge import EvidenceLevel, Signal, build_review_packet

packet = build_review_packet(
    Signal(
        title="Quebec deeptech digest service",
        summary="A public-safe weekly research, patent, and prototype digest service.",
        source_urls=("https://example.org/source",),
        domain="deeptech-intelligence",
        novelty_score=0.3,
        testability_score=0.8,
        revenue_score=0.9,
        disclosure_risk=0.1,
        evidence_level=EvidenceLevel.MULTI_SOURCE,
        tags=("quebec", "deeptech", "revenue"),
    )
)

print(packet.to_json())
```

## Verification

```bash
python -m pytest tests/test_omega_deeptech_forge.py tests/test_omega_deeptech_review_packets.py
```

## OAK boundary

This bridge is heuristic triage and packet preparation only. It is not legal advice, not a patentability opinion, not a revenue guarantee, and not an external automation engine.
