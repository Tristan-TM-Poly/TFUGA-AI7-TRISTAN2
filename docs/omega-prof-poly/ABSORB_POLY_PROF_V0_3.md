# Ω-ABSORB-POLY-PROF-T v0.3

Status: zero-touch public research absorption prototype.

## Purpose

Absorb public research metadata into ResearchAtoms, ProfessorResearchGenomes, and a PolyResearchTwin.

```text
public metadata / abstract
-> ResearchAtom
-> automated OAK packet
-> ProfessorResearchGenome
-> PolyResearchTwin
-> course/project/grant/IP opportunities
```

## Boundary

This module is designed for public metadata, abstracts, links, keywords, authors, claims, methods, limitations, datasets, and code links supplied by the caller.

It does not scrape or copy restricted full text. Full-text extraction belongs to a Rosette pipeline only when the source is open/licensed and provenance boundaries are retained.

## New modules

- `research_atom.py`: canonical public research atom with OAK compilation.
- `absorb_public_research.py`: public record ingestion into atoms and absorption reports.
- `professor_genome.py`: professor-level research genome builder.
- `poly_research_twin.py`: ecosystem-level opportunity twin.
- `course_memory_minus.py`: anti-error memory for CourseCVCD.
- `prior_art_packet.py`: IP-OAK prior-art planning packet.
- `schemas/omega_absorb_poly_prof_v0_3.schema.json`: schema for v0.3 packets.

## Commands

```bash
python examples/omega_absorb_poly_prof_v03_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v03.py
```

## OAK rules

- Absorb without copying restricted full text.
- Keep source link, source type, and absorption level.
- Separate claim, evidence, method, limitation, dataset, and code.
- Convert high-risk external actions into blocked-action packets.
- Use public metadata first; escalate to Rosette only when legal access is clear.

## Next v0.4 targets

1. deterministic JSON exports for ResearchAtom and PolyResearchTwin;
2. public metadata connector adapters;
3. ClaimGraph and MethodGraph modules;
4. integration with ProjectForge, GrantForge, IP-OAK Gate, and CourseCVCD;
5. generated Markdown reports for professor genomes.
