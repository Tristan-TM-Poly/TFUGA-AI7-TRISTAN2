# Ω-PROF-POLY-T — Professor Operating System for Polytechnique Montréal

Status: v0.1 OAK-safe zero-touch institutional prototype candidate.  
Scope: professor augmentation across teaching, research, labs, grants, IP, projects, and industry collaboration.

## Purpose

Ω-PROF-POLY-T turns professor-facing academic work into transparent, auditable, OAK-safe packets:

```text
course / paper / lab / project / grant idea / prototype
-> CVCD compression
-> ProfessorGraph-Poly
-> automated OAK risk and evidence audit
-> concrete next action or blocked external-action lock
```

It is not an automated professor, evaluator, administrator, IP attorney, or institutional authority. It is a zero-touch artifact-generation and decision-support layer: it does the routine work automatically, exposes evidence/risks, and blocks only actions that are irreversible, external, legally constrained, or missing technical authorization.

## Core thesis

```text
A professor is a high-value node in a living interdisciplinary hypergraph.
The system compresses their knowledge into better courses, labs, projects,
papers, grants, prototypes, and partnerships while preserving OAK boundaries.
Zero-touch is the default; manual verification is not a normal workflow step.
```

## Modules

- `ProfessorGraph-Poly`: graph of professors, courses, expertise, labs, equipment, students, partners, publications, patents, and projects.
- `CourseCVCD`: course compression into concepts, prerequisites, errors, exercises, labs, rubrics, AI-use rules, and project seeds.
- `StudentSkillTensor`: ethical skill tensor for team formation and support, never hidden automated ranking.
- `LabOAKBench`: lab protocol, uncertainty, error modes, reproducibility tests, and safety gates.
- `ResearchRosette`: paper-to-equations/code/claims/evidence/prototype/reproduction pipeline.
- `GrantWriter-OAK`: grant packet generator with feasibility, budget, risk, EDI, and impact checks.
- `IP-OAK Gate`: classifies outputs as public, confidential, patentable, trade secret, open source, or partner-ready.
- `Interdisciplinary Project Forge`: generates validated inter-engineering projects.
- `IndustryPartnerGraph`: connects expertise, prototypes, equipment, students, and partner needs.
- `OAK Academic Integrity Layer`: verifies permitted AI use, attribution, fairness, privacy, and evaluation boundaries.

## Executable MVP

This branch includes a dependency-free Python core:

```bash
python examples/omega_prof_poly_demo.py
python -m pytest tests/test_omega_prof_poly_t.py
```

The MVP ranks professor-facing opportunities by a transparent score:

```text
score = benefits - risk penalty + evidence bonus
```

Benefits include teaching, research, student, industry, IP, feasibility, reproducibility, and ethics/safety values.
Risks include confidentiality/IP, academic integrity, and overclaim risk.

## Zero-touch OAK boundary

- AI must augment professors, not replace them.
- Routine verification is automated by OAK, not deferred to manual checking.
- Every recommendation includes sources/evidence, limitations, uncertainty, risk, and next action.
- High confidentiality, academic integrity, medical/safety, or overclaim risks trigger an automated OAK gate and an external-action lock.
- Student evaluation, official policy changes, IP disclosure, publication, contract/signature, and institutional decisions are not claimed as autonomous authority by the model; they require a valid authorization channel before execution.
- Exploratory branches stay exploratory until proven, simulated, tested, or institutionally validated by evidence, not by manual ceremony.

## Release target

`omega-prof-poly-t-v0.1` can be tagged after:
1. tests pass;
2. at least one non-confidential course/lab/project pilot packet is added;
3. OAK/privacy/IP/integrity checks are encoded as automated gates;
4. the README links into the main repository canon.
