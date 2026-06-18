# v0.2 Execution Plan — THT/HGFM OAK Engine

Status: OAK-3 execution roadmap.  
Related issue: #29.

The purpose of v0.2 is to turn PR #21 from a canon seed into an operational research engine.

---

## 1. Merge gate for PR #21

Keep PR #21 in draft until:

- OAK Regression passes on the latest head commit;
- one human or OAK review pass checks public-facing language;
- experimental branches are clearly marked as test plans;
- no promoted claim lacks a report or test path.

---

## 2. Sprint order

### Sprint A — Formal math

Target: quaternionic HGFM hyper-Laplacian.

Outputs:

- randomized property tests;
- convention notes;
- comparison examples;
- proof cleanup.

Issue: #22.

### Sprint B — Corpus scanner

Target: zero-touch OAK corpus report.

Outputs:

- generated `oak_out/report.md`;
- claim-like lines;
- review candidates;
- registry updates.

Issue: #26.

### Sprint C — Raman benchmark

Target: spectral baseline comparison.

Outputs:

- real ALS baseline;
- multiple synthetic seeds;
- result table;
- OAKReport.

Issue: #23.

### Sprint D — Chess benchmark

Target: AIT-ChessMaster reproducible evaluation.

Outputs:

- minimal FEN set;
- legality checks;
- perft checks;
- optional engine comparison.

Issue: #24.

### Sprint E — Public communication

Target: professor-ready and reviewer-ready interface.

Outputs:

- professor brief;
- reviewer checklist;
- README public OAK section;
- preprint cleanup.

Issues: #27 and #31.

### Sprint F — Agent contracts

Target: safe SAGE/AIT operation.

Outputs:

- agent contract schema;
- agent contract examples;
- zero-touch boundary;
- review policy.

Issues: #30 and #32.

---

## 3. Definition of done for v0.2

v0.2 is done when the repo can answer:

1. What is the claim?
2. What is the status?
3. What is the evidence?
4. What is the residue?
5. What is the next test?
6. What is preserved as memory?

---

## 4. Non-goals

v0.2 does not need to solve every branch. It must make every branch testable, reviewable or safely parked.

---

## 5. Next best action after PR #21

Run:

```bash
python scripts/analyze_all.py . --out oak_out
```

Then review the generated report before promoting any new canon entries.
