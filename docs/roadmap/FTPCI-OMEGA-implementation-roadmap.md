# FTPCI-Ω Implementation Roadmap

**Branch:** `codex/ftpci-omega-tati-core`  
**Target:** executable v0.1 core for TATI / Alexandrie / HGFM / OAK.

---

## Phase 0 — Scope OAK

Goal: keep the v0.1 implementation small, testable, and non-mythological.

Must implement:

1. packet schema validation;
2. trace-to-packet conversion;
3. simple sparse tensor coordinate table;
4. fertility and OAK scoring;
5. selective decompression into a one-page codex;
6. memory-positive and memory-negative update logs.

Must not implement yet:

1. universal physics claims;
2. automatic proof of grand theories;
3. autonomous publication or uncontrolled external actions;
4. untraceable factor labels.

---

## Phase 1 — Canon Compiler v0.1

Input:

```text
raw idea / PDF excerpt / note / code comment
```

Output:

```text
FTPCI-Omega packet
```

Required fields:

- source;
- claim;
- concepts;
- hypotheses;
- risks;
- tensor coordinates;
- OAK status;
- fertility score;
- next action.

---

## Phase 2 — Sparse Tensor Table

Represent packets as rows:

```text
id | axiom | domain | invariant | operator | prototype | oak_status | fertility_band | memory_band
```

This is the first computable form of the Tristan tensor:

```math
T[a,d,i,e,p,o,f,m]
```

v0.1 does not need dense tensor math. It needs clean coordinates and sparse operations.

---

## Phase 3 — OAK Attack Engine v0.1

For each packet:

```text
claim -> attacks -> limits -> next verification
```

Minimum attack families:

1. missing definition;
2. missing test;
3. overclaim / hype;
4. hidden assumption;
5. contradiction with memory negative;
6. no prototype path.

---

## Phase 4 — Fertility Scoreboard

Initial score:

```math
F(x)=\frac{descendants + bridge\_domains + prototype\_path}{cost + risk + complexity + 1}
```

Priority:

```math
Priority(x)=\frac{F(x)\cdot OAK(x)}{Cost(x)\cdot Risk(x)+1}
```

The purpose is not perfect scoring. The purpose is useful triage.

---

## Phase 5 — Decompression 2^n v0.1

Start with:

- 1-page codex;
- 2-page codex;
- 4-page codex.

Each codex preserves:

```text
racines -> tronc -> branches -> feuilles -> fruits -> graines -> OAK
```

---

## Phase 6 — Residual Discovery

For each cycle, compute:

```math
R = claims_not_explained + contradictions + high_fertility_low_oak + missing_links
```

Then generate:

1. unresolved contradictions;
2. missing theory candidates;
3. prototype candidates;
4. memory-negative warnings.

---

## Phase 7 — Minimal Repository Deliverables

Recommended file targets:

```text
docs/canon/FTPCI-OMEGA-TATI-CORE-v0.1.md
schemas/ftpci_omega_packet.schema.json
examples/ftpci_omega_packet.example.json
sage_tristan/ftpci_omega.py
tests/test_ftpci_omega.py
reports/ftpci_omega_first_audit.md
```

---

## OAK Promotion Criteria

FTPCI-Ω can move from `prototype` to `local_validation` when:

1. at least 10 packets validate against schema;
2. scoring is deterministic;
3. one-page codex generation works;
4. memory-negative projection changes at least one future decision;
5. tests pass in CI.

---

## v0.1 Success Definition

```text
A small corpus enters.
Structured packets exit.
Packets become a sparse tensor table.
The table is scored.
Weak claims are attacked.
Fertile claims become a codex.
Errors become memory negative.
The next cycle is better than the first.
```

That is the executable seed of TATI.
