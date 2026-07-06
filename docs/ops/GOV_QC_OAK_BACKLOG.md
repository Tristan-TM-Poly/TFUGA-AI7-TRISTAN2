# Ω-GOV-QC-T — OAK Backlog

Status: B / Execution backlog
Date: 2026-07-06

## 1. OAK gates to implement

### LegalGate

- source authorization flag ;
- terms/license field ;
- responsible owner ;
- permitted use ;
- blocked use.

### PrivacyGate

- personal data indicator ;
- sensitivity level ;
- minimization plan ;
- anonymization or aggregation mode ;
- human review path.

### SecurityGate

- secret scanning ;
- access control checklist ;
- public/private data split ;
- logging requirement ;
- incident response note.

### FairnessGate

- affected groups field ;
- disproportional impact check ;
- explanation of limits ;
- correction path.

### ExplainabilityGate

- source list ;
- evidence list ;
- method ;
- uncertainty ;
- counter-explanations.

### HumanAuthorityGate

- human reviewer required ;
- authority owner ;
- escalation trigger ;
- appeal or correction path.

### EvidenceGate

- provenance ;
- hash ;
- retrieved_at ;
- version ;
- confidence ;
- reproducibility note.

### RobustnessGate

- unit tests ;
- example data ;
- schema validation ;
- malformed input tests ;
- M- registry.

### UtilityGate

- metric ;
- baseline ;
- expected improvement ;
- measurement plan ;
- cost estimate.

## 2. Issues to create later

1. Implement `SourceRegistry` with hash and provenance.
2. Implement `EvidenceGraph` and claim-source linking.
3. Implement `RiskTensor` scoring.
4. Implement Markdown report generation.
5. Add municipal example report.
6. Add schema validation tests.
7. Add OpenData ingestion adapter.
8. Add CLI `omega-gov-qc`.
9. Add NetworkX optional export.
10. Add GitHub Action for tests.

## 3. Blockers

- no production deployment before data-source policy is explicit ;
- no sensitive domains before PrivacyGate + HumanAuthorityGate are enforced ;
- no dashboard before output labels separate signal, evidence, recommendation and human decision ;
- no external publication before source licensing is checked.

## 4. Success definition for PR #223

This PR can graduate from draft when:

- package imports locally ;
- unit tests pass ;
- schemas are present ;
- OAKGate blocks high-impact contexts ;
- reports show limitations ;
- roadmap identifies next implementation work.
