# M− — Ω-OPEN-PROBLEMS-ATLAS-T∞ R0.1

| ID | Failure mode | Consequence | Permanent correction |
|---|---|---|---|
| OPA-M-001 | Counting generated research slots as verified open problems | Inflated corpus and false progress | `ResearchCell.is_verified_open_problem` defaults to false and the seed manifest reports the verified count separately. |
| OPA-M-002 | Treating a source label as an independent status check | Work invested in stale or solved problems | `SOURCE_REPORTED_OPEN` is routed to `DISCOVERY_ONLY`; dated literature review is required for promotion. |
| OPA-M-003 | Treating finite computation as proof | Invalid universal claim | Every genome and cell carries `finite_computation_is_not_proof=true`; removing it blocks OAK. |
| OPA-M-004 | Mixing contests with research-open problems | Corrupted metrics and rule violations | Distinct `ProblemKind` values and source policies; competition records never enter open-problem counts automatically. |
| OPA-M-005 | Duplicate statements under different identifiers | Fragmented attempts and wasted compute | SHA-256 normalized-statement deduplication in `ProblemRegistry`. |
| OPA-M-006 | Large GitHub diff interpreted as mathematical progress | Incentive misalignment | Report code, tests, sourced genomes, verified statuses, partial results and independent reproductions separately. |
| OPA-M-007 | Publishing a claimed solution automatically | Reputational and scientific harm | Human review is mandatory; OAK returns `RESULT_REVIEW_REQUIRED` or `BLOCK`. |
| OPA-M-008 | Mirroring copyrighted problem descriptions or contest data | Licensing and attribution risk | Store normalized metadata, citations and only content allowed by each source license. |
| OPA-M-009 | Transferring a method because two problems share vocabulary | Spurious connections | Every transfer edge must specify assumptions, round-trip checks, baselines and failure conditions. |
| OPA-M-010 | Letting monumental problems consume all resources | Few feedback cycles and weak skill calibration | Maintain a portfolio of monumental, intermediate, tractable, formalization and competition tasks. |
