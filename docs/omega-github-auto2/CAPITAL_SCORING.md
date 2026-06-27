# Omega AUTO2 Capital Scoring

Each card receives an E-cap score from 0 to 100.

## v2 weights

| Factor | Weight | Meaning |
|---|---:|---|
| Revenue short term | 0.14 | Can it create near-term API, pilot, or ARR value? |
| Proof measurable | 0.12 | Can it be benchmarked or falsified? |
| Moat retention | 0.12 | Does it increase customer lock-in or memory value? |
| Market demand | 0.10 | Is there clear demand? |
| IP potential | 0.10 | Could it become defensible know-how or patentable material? |
| Zero-touch | 0.10 | Can it operate with little manual effort? |
| API scalability | 0.08 | Can it scale as a SaaS/API primitive? |
| B2B compliance | 0.08 | Can it survive enterprise review? |
| Time to value | 0.08 | How quickly can it prove value? |
| Leverage | 0.08 | How many future cards does it unlock? |

## Priority bands

- `P0`: immediate execution queue.
- `P1`: high leverage or moat.
- `P2`: expansion backlog.
- `P3_STEALTH_IP`: protected IP / review-only.
- `P4_RESEARCH`: speculative or delayed.

## Rule

A high score does not override OAK. A high-value card can remain blocked if it has IP, regulated, billing, or safety risk.
