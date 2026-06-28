# Ω-PROF-POLY-T — Best Novelties Analysis

Status: post-v0.2 analysis report.  
Mode: zero-touch by default.  
Date: 2026-06-28.

## Executive ranking

| Rank | Novelty | Score | Why it matters | Next action |
|---:|---|---:|---|---|
| 1 | OAK as automated compiler | 0.96 | Converts an artifact into score, risks, warnings, status, next action, and blocked-action packet. | Expand to OAKCompiler v0.3 with evidence ledger and JSON export. |
| 2 | CourseCVCD executable engine | 0.91 | Converts course objectives into concept graph, exercise seeds, project seeds, rubric axes, and OAK packet. | Add misconception memory and exercise generator. |
| 3 | ProjectForge inter-engineering engine | 0.89 | Turns needs, disciplines, prototypes, equipment, and term length into deliverables, success tests, and publication/IP/startup potential. | Add portfolio optimizer and project backlog generator. |
| 4 | IP-OAK Gate | 0.88 | Routes results toward publish, patent candidate, open source, trade secret, license candidate, or hold-for-evidence. | Add prior-art search packet and disclosure-risk ledger. |
| 5 | ProfessorGraph-Poly | 0.86 | Introduces a lightweight hypergraph connecting professor, course, lab, project, prototype, and partner nodes. | Add import/export and real public expertise ingestion. |
| 6 | LabOAKBench | 0.84 | Turns lab hypotheses into protocol steps, uncertainty sources, coherence tests, and artifact controls. | Add synthetic data stubs and script generator. |
| 7 | GrantForge-OAK | 0.82 | Generates grant packet sections and a grant score, with external-action lock for submissions. | Add program-target matching and budget stub. |
| 8 | Markdown report renderer | 0.74 | Gives all packet types a common report path. | Add deterministic report snapshots and JSON/Markdown dual export. |

## 1. Strongest novelty: OAK as compiler

The main conceptual upgrade is that OAK is no longer just an audit principle. In `zero_touch_oak.py`, it is executable: `compile_oak` transforms benefits, risks, evidence count, and external-action status into a structured `OAKCompileResult`.

Core outputs:

```text
status
score
evidence_count
risks
benefits
warnings
next_action
blocked_action
```

Best features:

- `GateStatus` cleanly separates safe workspace generation, auto-generate-only, external-action lock, and blocked states.
- `BlockedActionPacket` preserves zero-touch flow: the artifact remains ready even when external execution is not possible.
- Risk warnings are machine-readable: `no_evidence_attached`, `high_risk_requires_auto_gate`, `run_ip_and_confidentiality_gate`, etc.

OAK-safe interpretation:

```text
No manual review as default.
Routine checks become compiler outputs.
External or irreversible actions become capability boundaries, not workflow stops.
```

## 2. CourseCVCD novelty

`coursecvcd.py` is the first real course-to-artifact compiler.

It creates:

- `CourseInput`
- `ConceptNode`
- `CourseCVCDPacket`
- concept graph from objectives
- exercise seeds
- project seeds
- rubric axes
- automated OAK packet

This is powerful because it turns a course from static notes into a generative object:

```text
course objectives
-> concept graph
-> exercises
-> projects
-> rubric
-> OAK packet
```

Next improvement:

```text
Add CourseMemoryMinus:
common student errors -> anti-error rules -> exercise variants -> rubric warnings.
```

## 3. ProjectForge novelty

`project_forge.py` creates a practical bridge from research and teaching into projects.

It scores:

- publication potential;
- IP potential;
- startup potential;
- feasibility;
- complexity;
- overclaim risk;
- equipment dependency.

This is one of the most monetizable pieces because it can create project backlogs for courses, labs, professors, industry partners, and startups.

Next improvement:

```text
Add ProjectPortfolioOptimizer:
maximize interdisciplinarity + feasibility + prototype value + OAK score.
```

## 4. IP-OAK Gate novelty

`ip_oak_gate.py` is strategically important because it protects the transition from research to value.

It routes outputs to:

```text
publish
patent_candidate
open_source
trade_secret
license_candidate
hold_for_evidence
```

Best design choice:

```text
patent/license/trade_secret routes automatically trigger external-action lock.
```

This preserves zero-touch generation while preventing the system from pretending it can execute legal/commercial steps without platform capability.

Next improvement:

```text
Add PriorArtPacket:
keywords, novelty axis, closest public references, risk, recommended disclosure path.
```

## 5. ProfessorGraph-Poly novelty

`professor_graph.py` gives the system a minimal hypergraph backbone.

It currently supports:

- nodes;
- hyperedges;
- neighbor lookup;
- graph hole detection;
- auto-questions such as courses that can become labs and prototypes partner-ready.

This is the bridge toward PolyResearchTwin.

Next improvement:

```text
Add graph import/export:
JSON -> ProfessorGraph -> questions -> reports.
```

## 6. LabOAKBench novelty

`lab_oakbench.py` converts a lab hypothesis into:

- protocol steps;
- uncertainty sources;
- coherence tests;
- artifact controls;
- automated OAK packet.

This directly supports engineering education because a lab becomes a falsification machine, not just a demonstration.

Next improvement:

```text
Add LabScriptForge:
LabOAKBenchPacket -> Python analysis script stub -> deterministic test.
```

## 7. GrantForge-OAK novelty

`grant_forge.py` creates a grant packet and grant score.

It is not yet a full grant writer, but the skeleton is correct:

```text
title + problem + objectives + methods
-> public summary
-> scientific summary
-> workpackages
-> risk plan
-> score
-> OAK packet
```

Next improvement:

```text
Add ProgramMatcher:
project cluster -> CRSNG/FRQ/Mitacs/Horizon/industry-fit packet.
```

## 8. Best architecture insight

The strongest architecture pattern is this unified packet grammar:

```text
Input object
-> domain compiler
-> OAKCompileResult
-> report renderer
-> next action
```

Every module now has the same destiny:

```text
CourseCVCDPacket
LabOAKBenchPacket
ProjectPacket
GrantPacket
IPGatePacket
ProfessorGraph answer packet
```

This is the seed of a real Professor Operating System.

## M-minus findings

| Issue | Severity | Fix |
|---|---:|---|
| Scoring weights are still heuristic | High | Add calibrated weights and benchmark examples. |
| No JSON schema v2 for zero-touch packets | High | Add `omega_prof_poly_packet_v2.schema.json`. |
| No real public ingestion yet | High | Add PolyPublie/Expertise demo ingestion using public metadata only. |
| CourseCVCD uses simple objective mapping | Medium | Add concept extraction, prerequisite graph, and misconception memory. |
| ProfessorGraph is in-memory only | Medium | Add import/export and graph reports. |
| Report renderer has no snapshot tests | Medium | Add deterministic report fixtures. |
| IPGate is not legal advice | High | Keep as triage packet only; add explicit OAK boundary. |

## Recommended v0.3 backlog

1. `schemas/omega_prof_poly_packet_v2.schema.json`
2. `omega_prof_poly_t/research_atom.py`
3. `omega_prof_poly_t/absorb_public_research.py`
4. `omega_prof_poly_t/professor_genome.py`
5. `omega_prof_poly_t/poly_research_twin.py`
6. `omega_prof_poly_t/course_memory_minus.py`
7. `omega_prof_poly_t/lab_script_forge.py`
8. `omega_prof_poly_t/prior_art_packet.py`
9. `examples/research_atom_demo.json`
10. `tests/test_absorb_public_research.py`

## Best immediate command

```text
GO @GitHub Ω-ABSORB-POLY-PROF-T v0.3
```

Target:

```text
Public metadata ingestion
-> ResearchAtom
-> ProfessorResearchGenome
-> ClaimGraph/MethodGraph seed
-> OAKCompiler
-> Course/Project/Grant/IP opportunities
```

## Final verdict

The best novelty is not any single module. It is the conversion of the whole Ω-PROF-POLY-T branch into a reusable compiler pattern:

```text
academic artifact
-> domain compiler
-> automated OAK
-> packet
-> report
-> next action
```

This makes the system scalable from one professor to a department, then to all of Poly, then to the broader Quebec research ecosystem.
