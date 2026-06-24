# OAKReport example — Quaternionic HGFM hyper-Laplacian

```yaml
id: OAK-REPORT-0001
claim: "Quaternionic HGFM hyper-Laplacian L = B W B dagger is Hermitian positive semidefinite when W is real diagonal nonnegative."
claim_type: theorem
scope: "HGFM math / quaternionic hyper-Laplacian"
status_before: FORMALIZED
challenge:
  questions:
    - "Are the quaternion conventions explicit?"
    - "Does the proof handle non-commutativity correctly?"
    - "Are eigenvalue conventions stated?"
  review_checks:
    - "Generate random quaternionic B and nonnegative W."
    - "Convert to complex representation and test Hermitian symmetry."
    - "Check quadratic energy is nonnegative for random vectors."
evidence:
  artifacts:
    - "docs/theory/hgfm_quaternion_laplacian_theorem.md"
    - "tests/test_quaternion_laplacian.py"
  tests:
    - "OAK Regression pytest workflow"
  reproduction:
    - "python -m pytest tests/test_quaternion_laplacian.py"
residue:
  known_limits:
    - "Not yet formalized in Lean or Coq."
    - "Right and left quaternionic eigenvalue conventions must be stated."
  uncertainty:
    - "Numerical representation depends on convention."
verdict: promote_conditionally
status_after: SIMULATION_READY
next_test: "Add randomized property tests and invalid-W comparison examples."
reviewer: "OAK-Validator"
created_at: "2026-06-18T19:30:00Z"
links:
  - "PR #21"
  - "Issue #22"
```
