# R7 — All-orders Stieltjes/Hankel bridge to RH

Status: `CLOSED_BY_R10`, `HISTORICAL_DRAFT`, `NOT_A_RH_PROOF`.

R7 was the draft that isolated the all-orders Stieltjes/Hankel route. Its proof
obligations have now been discharged in the canonical document:

- [`R10_STIELTJES_HANKEL_EQUIVALENCE.md`](R10_STIELTJES_HANKEL_EQUIVALENCE.md)

R10 proves the **derived equivalence criterion**

\[
RH
\iff
(m_k)_{k\ge0}\text{ is a Stieltjes moment sequence}
\iff
H_N^{(0)},H_N^{(1)}\succeq0\text{ for every }N.
\]

It also proves the contrapositive existential corollary

\[
RH\text{ false}
\Longrightarrow
\exists N<\infty:
H_N^{(0)}\not\succeq0
\text{ or }
H_N^{(1)}\not\succeq0.
\]

This does **not** prove RH because it does not establish all-orders positivity.
It only supplies another condition equivalent to RH.

The R7 draft is retained as M+/provenance showing how the proof program evolved.
Do not cite it as the canonical proof; use R10.

Novelty is also blocked: close 2026 prior art on Hankel/Jacobi positivity of
secondary-zeta moments has been found and is recorded in the bibliography
ledger pending full-text comparison.
