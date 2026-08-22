# Ω-POLYSPECIALIST-T — multi-specialization compiler

Status: OAK-safe prototype integrated into `omega_prof_poly_t`.

## Thesis

The target is not one narrow specialty and not shallow accumulation. It is **poly-specialization**:

```text
strong common core
+ several deep axes
+ deliberate bridges between axes
+ degree completion
+ research/prototype artifacts
```

The compiler treats a term as a constrained portfolio problem. It prioritizes required degree progress, repeat/repair value, marginal specialization coverage, and courses that bridge several axes while respecting prerequisites, term availability, workload, credit budget, and evidence freshness.

## Default axes

- quantum
- photonics
- nano/materials
- energy/nuclear
- biomedical
- computation/AI
- electronics/instrumentation
- mechanics/thermal
- entrepreneurship/governance

The list is configurable and can be expanded to controls, robotics, fluids, plasma, chemistry, software, mathematics, geophysics, or other validated domains.

## Core API

`omega_prof_poly_t.student_polyspecialist` provides:

- `CourseCandidate`
- `StudentProfile`
- `PlanWeights`
- `PlannedCourse`
- `MultiSpecializationPlan`
- `EvidenceState`
- `compile_polyspecialist_plan`
- `render_polyspecialist_markdown`

## Objective

For every eligible candidate course, the compiler builds a transparent marginal score from:

```text
required degree value
+ repeat/repair value
+ graduation progress
+ newly covered axes
+ bridge density
+ verified-source bonus
- workload penalty
- stale/unverified evidence penalty
```

The score is a heuristic and is not claimed to be a proof of global optimality.

## OAK registration gate

A generated plan is decision support, not an official registration action. Operational use must verify authoritative institutional information for:

1. program/cohort degree requirements;
2. credit attribution;
3. prerequisites and corequisites;
4. current course and section offerings;
5. timetable conflicts;
6. registration restrictions;
7. graduation eligibility;
8. full-time/part-time consequences where relevant.

`verified`, `unverified`, `stale`, and `blocked` evidence states prevent a plausible plan from being silently treated as institutional truth.

## Privacy boundary

The public module is deliberately privacy-minimized. It needs only aggregate planning state such as completed course codes, earned-credit totals, missing required codes, desired axes, and term budget. Private academic records do not belong in the public repository.

## Architecture

```text
verified academic inputs
        |
        v
StudentProfile + CourseCandidate catalog
        |
        v
eligibility filter
(prerequisites / term / source state)
        |
        v
required-course pass
        |
        v
marginal coverage + bridge compiler
        |
        v
MultiSpecializationPlan
        |
        +--> axis coverage
        +--> degree progress
        +--> workload/credit checks
        +--> OAK warnings
        +--> registration gate
```

## Research meaning of "specialize in everything"

Breadth becomes defensible only when every major axis eventually acquires depth evidence. A later StudentSkillTensor should distinguish:

- exposure;
- completed coursework;
- demonstrated problem solving;
- reproducible code;
- laboratory competence;
- project artifacts;
- research contribution;
- independent verification.

Thus a label such as `quantum` or `biomedical` is never by itself evidence of expertise.

## GO MAX roadmap

### R0.1 — current PR

- multi-axis course representation;
- privacy-minimized student profile;
- required-course priority;
- repeat/repair priority;
- prerequisite filtering;
- term filtering;
- marginal axis coverage;
- multi-axis bridge reward;
- workload and credit-budget accounting;
- evidence freshness states;
- OAK status and registration-readiness;
- deterministic tests;
- Markdown renderer.

### R0.2 — tracked separately

- authoritative read-only program/catalog adapter with provenance and timestamps;
- section-level timetable model;
- prerequisite DAG / HGFM;
- constrained no-conflict portfolio solver;
- deterministic fixture catalog;
- cohort-aware degree audit;
- axis-depth metrics;
- research bridge compiler.

### R0.3+

Build a private Personal Academic Twin that compiles bachelor, graduate courses, laboratories, research projects, professors, equipment, publications, and prototypes into a long-horizon breadth/depth frontier.

## M-minus anti-errors

- Do not equate many courses with expertise.
- Do not sacrifice mandatory degree completion for optional novelty.
- Do not treat outdated course metadata as current truth.
- Do not select courses with unmet hard prerequisites.
- Do not expose private academic records in a public repository.
- Do not optimize GPA, credits, novelty, or breadth as a single objective.
- Do not claim global optimality for the greedy compiler.
- Do not execute registration changes without authorized human action.

## Long-horizon quality vector

```text
Q_poly = (
    degree_progress,
    verified_axis_depth,
    axis_breadth,
    bridge_density,
    artifact_count,
    research_depth,
    reproducibility,
    uncertainty,
    workload_sustainability
)
```

This turns "specialize in everything" into a measurable research-and-training program rather than an unbounded accumulation slogan.
