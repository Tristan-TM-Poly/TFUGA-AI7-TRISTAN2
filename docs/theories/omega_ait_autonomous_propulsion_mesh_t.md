# Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T
## Le réseau de propulsion autonome OAK-safe des AIT de Tristan

> **Status:** canonical layer above ContinuationEngine.  
> **Hard boundary:** AutonomousPropulsionMesh coordinates safe, reversible, traceable work. It does not auto-merge, publish, deploy, contact external parties, make high-impact decisions, or bypass review gates.

## 0. Idée mère

ContinuationEngine dit:

```math
\boxed{\text{Every state must produce a safe next move.}}
```

AutonomousPropulsionMesh ajoute:

```math
\boxed{\text{Every safe next move must spawn the next useful chain of moves.}}
```

L'AIT ne produit plus seulement une action suivante. Il produit une trajectoire auto-entretenue:

```text
Goal -> SafeAction -> Artifact -> Test -> Audit -> CanonUpdate -> NextGoal -> NextChain
```

```math
\boxed{AIT_{Propulsion}=ContinuationEngine+TaskQueues+PriorityEngine+DebtBurner+SelfRepair+ArtifactSwarm+OAKGovernor+M^-}
```

## 1. Multi-Queue Autonomy

Files autonomes:

```text
Q0 ideas_to_anchor
Q1 theories_to_formalize
Q2 tools_to_create
Q3 tests_to_add
Q4 benchmarks_to_build
Q5 oak_reports_to_write
Q6 m_minus_to_record
Q7 debts_to_burn
Q8 prs_to_enrich
Q9 branches_to_canonize
Q10 quarantined_tasks
```

Règle:

```math
\boxed{\text{If one queue is blocked, advance another safe queue.}}
```

## 2. DebtBurner Engine

Toute dette visible devient une tâche générable:

```text
proof_debt -> test or benchmark
risk_debt -> OAK report
test_debt -> test skeleton
source_debt -> source status note
rollback_debt -> rollback plan
canon_link_debt -> CanonGraph edge
```

```math
\boxed{\text{Une dette visible est déjà une tâche générable.}}
```

## 3. Self-Repair Loop

Quand un module casse, il produit:

```text
failure_packet
minimal_reproduction
failing_test
suspected_cause
safe_patch_plan
rollback_note
M- entry
next_patch
```

```math
Failure\rightarrow Reproduction\rightarrow Test\rightarrow Patch\rightarrow Audit\rightarrow M^-\rightarrow StrongerSystem
```

Loi:

```math
\boxed{\text{Un bug non transformé en test est une perte de connaissance.}}
```

## 4. ArtifactSwarm

Chaque objectif cherche son prochain artefact naturel:

```text
theory.md
schema.json
tool.py
test_tool.py
policy.yaml
m_minus.yaml
oak_report.md
roadmap.md
example.md
benchmark.md
```

Examples:

```text
idea_without_proof -> test_tool.py
tool_without_benchmark -> benchmark.md
theory_without_structure -> schema.json
unhandled_risk -> oak_report.md
repeated_error -> m_minus.yaml
fertile_branch -> roadmap.md
```

## 5. SafeFork Engine

Quand une décision est incertaine, créer des forks sûrs:

```text
fork_A prototype_minimal
fork_B benchmark_only
fork_C oak_report
fork_D theory_refinement
fork_E m_minus_registry
```

Puis comparer utility, risk, cost, testability, canon_gain, rollback.

## 6. OAK Governor

OAK n'est pas un frein; OAK est le système de direction.

```text
safe -> continue
uncertain -> simulate
weak_proof -> test
public_risk -> review_packet
private_risk -> scrub_or_private_note
irreversible -> hold_direct_action_and_produce_dossier
high_risk -> quarantine_and_m_minus
```

## 7. Human-Zero Routine

Tristan ne doit pas vérifier les détails routiniers. L'AIT auto-vérifie syntaxe, cohérence, tests, niveaux R/P/C/B, risques, rollback, privacy/IP et frontières OAK.

```math
\boxed{\text{Tristan valide les seuils de souveraineté; l'AIT vérifie tout le reste.}}
```

## 8. Autonomous Sprint Cell

Chaque sprint sûr produit:

```text
1 artifact created
1 test or validation added
1 debt reduced
1 next safe move
```

## 9. Infinite Useful Work

Même si une voie est bloquée, il reste du travail utile: index, tests, docs, CanonGraph links, debt classification, M-, OAK reports, review packets, examples, README, benchmark skeletons.

```math
\boxed{\text{Il existe toujours un travail utile, sûr, réversible et canonique.}}
```

## 10. Progress Memory

Chaque mouvement trace:

```text
what_changed
why
risk
evidence
test
residue
M-
next_safe_action
```

## 11. Propulsion Equation

```math
PropulsionScore=Impact+CanonGain+DebtReduction+Testability+Reversibility-Risk-Cost-Uncertainty-Irreversibility
```

## 12. Final law

```math
\boxed{\text{L'AIT de Tristan ne cherche pas seulement la prochaine action; il entretient une propulsion autonome de tâches sûres, traçables, testables et canonisables.}}
```

Supreme law:

```math
\boxed{\text{If one path is blocked, advance another safe path.}}
```
