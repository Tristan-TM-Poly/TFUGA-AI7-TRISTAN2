# AIT-ChessMaster OAK Benchmark

Status: OAK-3 benchmark protocol seed.  
Related issue: #24.

Chess is a strong OAK laboratory because many claims can be checked against deterministic or high-quality references.

---

## 1. Goal

Evaluate AIT-ChessMaster through reproducible chess tasks rather than subjective impressions.

Core principle:

```text
No chess intelligence claim without a reference check.
```

---

## 2. Reference checks

Use:

- perft node counts for legal move generation;
- simple endgame tablebases when available;
- fixed-depth Stockfish evaluation when available;
- curated tactical FEN positions;
- repeated-blunder tracking through negative memory.

---

## 3. Metrics

| Metric | Meaning |
|---|---|
| legal_move_validity | proposed moves are legal |
| perft_match | node counts match reference values |
| best_move_match | agreement with reference engine |
| centipawn_loss | value drop vs reference move |
| tablebase_wdl_match | win/draw/loss correctness in solved endings |
| repeated_error_rate | repeated mistakes after memory update |

---

## 4. Minimal dataset

Start with:

```text
experiments/chessmaster_oak/fens_minimal.txt
```

Containing:

- starting position;
- tactical motif;
- simple king-pawn ending;
- checkmate-in-one;
- illegal-move trap;
- quiet positional position.

---

## 5. OAK report per run

Each run should output:

```text
position_id
fen
move_proposed
reference_move
legal
score_delta
verdict
residue
next_test
```

---

## 6. Promotion criteria

A ChessMaster module can move from concept to benchmark-ready if it:

- runs on a fixed FEN set;
- logs every move;
- checks legality;
- compares to at least one reference;
- records repeated failures.

It can move beyond benchmark-ready only after reproducible results.

---

## 7. Next minimal implementation

1. Add `experiments/chessmaster_oak/fens_minimal.txt`.
2. Add a pure-Python FEN reader or optional `python-chess` integration.
3. Add perft tests for known positions.
4. Add optional Stockfish integration behind an availability check.
5. Emit OAKReport JSON or YAML per benchmark run.
