# Ω-PROF-POLY-T — Professor Operating System for Polytechnique Montréal

Status: v0.1 OAK-safe institutional prototype candidate.  
Scope: professor augmentation across teaching, research, labs, grants, IP, projects, and industry collaboration.

## Purpose

Ω-PROF-POLY-T turns professor-facing academic work into transparent, auditable, OAK-safe packets:

```text
course / paper / lab / project / grant idea / prototype
-> CVCD compression
-> ProfessorGraph-Poly
-> OAK risk and evidence audit
-> concrete next action
```

It is not an automated professor, evaluator, administrator, IP attorney, or institutional decision-maker. It is a decision-support and artifact-generation layer that keeps the professor, department, and institution in control.

## Core thesis

```text
A professor is a high-value node in a living interdisciplinary hypergraph.
The system helps compress their knowledge into better courses, labs, projects,
papers, grants, prototypes, and partnerships while preserving OAK boundaries.
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

## OAK boundary

- AI must augment professors, not replace them.
- Student evaluation, academic judgment, IP disclosure, and institutional decisions remain human-governed.
- Every recommendation should include sources/evidence, limitations, uncertainty, risk, and next action.
- High confidentiality, academic integrity, medical/safety, or overclaim risks block automated deployment.
- Exploratory branches stay exploratory until proven, simulated, tested, or institutionally validated.

## Release target

`omega-prof-poly-t-v0.1` can be tagged after:
1. tests pass;
2. at least one real course/lab/project pilot packet is added with consent;
3. an institutional OAK/privacy/IP review checklist is completed;
4. the README links into the main repository canon.
