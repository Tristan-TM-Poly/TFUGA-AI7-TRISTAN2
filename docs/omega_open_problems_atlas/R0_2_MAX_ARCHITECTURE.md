# Ω-OPEN-PROBLEMS-ATLAS-T∞ R0.2 MAX

## Status

`SOFTWARE_RESEARCH_ARCHITECTURE / HUMAN_MATHEMATICAL_REVIEW_REQUIRED`

R0.2 extends the R0.1 `ProblemGenome` seed into a durable research operating
system. It does not claim a new theorem, an independently verified open status,
a competition entry, a formal proof or a solution to any Clay problem.

## Mother objective

Convert many heterogeneous mathematical problems, conjectures, competition
archives and computational challenges into a governed network of:

- sourced problem leads;
- normalized statements;
- proof obligations;
- reusable methods;
- transfer hypotheses;
- finite experiments;
- formalization tasks;
- evidence receipts;
- negative memory;
- independently reviewable research packets.

The objective is not to maximize line count. The objective is to maximize the
number of reusable, falsifiable and provenance-preserving mathematical assets.

## Permanent distinctions

```text
SOURCE_REPORTED != INDEPENDENTLY_CHECKED_OPEN
GENERATED_FIXTURE != REAL_OPEN_PROBLEM
COMPETITION_PROBLEM != RESEARCH_OPEN_PROBLEM
FINITE_COMPUTATION != UNIVERSAL_PROOF
FORMAL_SKELETON != COMPLETED_FORMAL_PROOF
METHOD_SIMILARITY != MATHEMATICAL_EQUIVALENCE
TRANSFER_HYPOTHESIS != VALIDATED_TRANSFER
PRIORITY_SCORE != PROBABILITY_OF_TRUTH
MANY_ADDITIONS != MATHEMATICAL_PROGRESS
```

## R0.2 object model

### SourceSnapshot

A source snapshot records the source identifier, retrieval time, authority
class, license class, content hash and status policy. The core package does not
scrape the network. It consumes local snapshots prepared by source-specific,
rules-aware collection jobs.

### ProblemLead

A `ProblemLead` is not automatically an open problem. It stores:

- source and locator;
- short normalized statement summary;
- domains and type;
- methods and related identifiers;
- source snapshot hash;
- license-review state;
- literature-search requirement;
- explicit open-status state;
- permanent anti-overclaim flags.

Promotion to `INDEPENDENTLY_CHECKED_OPEN` requires a separate current
literature review and human mathematical review.

### MethodCard

A method card stores a reusable mathematical technique, its domains,
prerequisites, implementations, formalizations and known failure modes. R0.2
materializes 128 deterministic method fixtures across sixteen method families
for software validation. These fixtures are not claims that the methods solve a
real problem.

### ProofObligation

R0.2 defines 64 obligation operators, including:

- statement, quantifier, assumption and definition audits;
- bidirectional equivalence checks;
- algebraic, geometric, spectral, probabilistic and variational formulations;
- finite, low-dimensional, symmetric, extremal and degenerate cases;
- upper and lower bounds;
- exact, interval, symbolic, SAT/SMT and graph-search probes;
- negative controls and ablations;
- formal definitions, known lemmas and candidate lemmas;
- citation, license and status audits;
- method-transfer round trips;
- independent reproduction and human expert review.

Every campaign invocation has a finite explicit budget. The architecture stores
no permanent total cap.

### TransferEdge

A transfer edge is a hypothesis that a declared method or invariant may move
between two problem families. Every edge starts unvalidated and requires a
reverse or round-trip check. Shared vocabulary alone is not evidence of a valid
mathematical reduction.

### EvidenceReceipt

Evidence receipts are hash-addressed records linking a subject to:

- evidence class;
- artifact SHA-256;
- command;
- environment;
- observation time;
- result;
- parent receipt;
- bounded claim scope.

Receipts can be committed, stored in SQLite or bundled into Merkle manifests.

## Source architecture

`data/open_problems_atlas/r02/source_connectors.json` defines governed source
classes. The connector catalog covers official prize lists, curated problem
lists, specialist databases, community sources, literature graphs, historical
collections, formal and competition archives, and user-authorized local notes.

The core library enforces:

```text
network_collection = DISABLED_IN_CORE
automatic_open_status_promotion = false
automatic_competition_submission = false
full_statement_mirroring_default = false
independent_literature_check_required = true
```

This prevents a generated or scraped record from silently becoming a claimed
open problem.

## Competition boundary

Competition and challenge records are tracked separately because they differ
from research-open problems in at least four ways:

1. they may already have official solutions;
2. rules, deadlines and AI policies can change;
3. submissions can be identity-bound;
4. datasets and problem statements can have restrictive licenses.

The default policy permits local metadata and private training fixtures. It
blocks automated identity-bound submission, stale-rule reliance and mirroring
without permission.

## Sensitive-data boundary

The intake layer rejects snapshots containing forbidden sensitive fields such
as passwords, tokens, private keys, tax identifiers or banking coordinates.
The atlas has no schema for banking data, identity documents or private
correspondence.

## Durable storage

The SQLite registry uses:

- WAL journaling;
- foreign-key enforcement;
- transactional batches;
- unique source-locator constraints;
- statement and canonical hashes;
- separate tables for leads, methods, obligations, transfers, receipts,
  negative memory and checkpoints;
- checkpoint Merkle roots.

Large campaigns stream obligations into SQLite rather than materializing every
object in memory.

## Deduplication

R0.2 provides two levels:

- exact duplicate groups using normalized statement hashes;
- conservative lexical near-duplicate findings inside bounded buckets.

Lexical similarity is only a review signal. It is not a proof that two
mathematical statements are equivalent.

## Formalization gate

The formal audit recognizes common placeholders in Lean, Coq and Isabelle.
Files containing `sorry`, `admit`, `Admitted` or equivalent markers are blocked
from formal promotion. Absence of a placeholder is still insufficient: a local
kernel check and, for stronger status, an independent rebuild receipt are
required.

## Adaptive campaign allocation

R0.2 uses a transparent multiplicative research-value score with axes such as:

- impact;
- transferability;
- testability;
- formalizability;
- source confidence;
- difficulty;
- uncertainty;
- maintenance cost.

The score allocates research budget; it is never presented as the probability
that a statement is true. Weighted round-robin allocation prevents a single
famous problem from starving the rest of the portfolio.

## Address space

R0.2 defines:

```text
64 mathematical domains
× 64 obligation operators
× 128 method cards
× 32 result classes
× 16 evidence modes
= 268,435,456 logical research cells
```

The logical frontier is indexed, not committed as hundreds of millions of JSON
records. The distinction is explicit:

```text
logical_frontier_materialized = false
```

This preserves the ability to navigate an enormous search space without
pretending to have created or verified 268 million open problems.

## Materialized software fixtures

The standard matrix materializes:

```text
512 synthetic problem leads
128 synthetic method cards
10,001 proof obligations
bounded transfer samples
SQLite checkpoint
Merkle proof
```

The dedicated scale gate materializes:

```text
4,096 synthetic problem leads
128 synthetic method cards
250,000 streamed proof obligations
SQLite WAL registry
Merkle checkpoint
```

All synthetic leads state that they are fixtures. The expected independently
checked open-problem count and solution-claim count are both zero.

## CI gates

Python 3.10 through 3.13 must each:

- compile R0.1 and R0.2;
- run focused tests;
- generate the deterministic benchmark twice;
- compare outputs byte-for-byte;
- validate JSON Schemas;
- validate the logical frontier;
- confirm exact counts;
- confirm a valid Merkle inclusion proof;
- confirm zero independently checked synthetic problems;
- confirm zero solution claims;
- confirm no automated external submission.

A separate Python 3.13 scale job must pass the 250,000-obligation campaign.

## Research promotion ladder

```text
DISCOVERED
→ SOURCE_REPORTED
→ LICENSE_REVIEWED
→ STATUS_RECHECKED
→ NORMALIZED
→ LITERATURE_BASELINED
→ DECOMPOSED
→ FINITELY_PROBED
→ PARTIAL_PROGRESS
→ INDEPENDENTLY_REPRODUCED
→ FORMALLY_CHECKED_OR_PEER_REVIEWED
→ CANON_CANDIDATE
```

A record can also move to:

```text
RESOLVED
DISPUTED
STALE
DUPLICATE
REJECTED
M_MINUS
```

## Intended R0.3

R0.3 should add real source-specific snapshot builders and start a reviewed
intake queue. The target is hundreds of normalized source leads, but each one
must preserve its upstream identifier, citation, current status uncertainty,
license decision and last literature check.

No bulk import should claim that all collected items remain open. The correct
output of an import is a review queue, not a theorem registry.

## OAK declaration

R0.2 demonstrates research-software invariants on declared fixtures. It does
not demonstrate:

- that any imported problem is currently open;
- that any generated obligation is mathematically useful;
- that any method transfer is correct;
- that any competition permits a specific use of AI;
- that any computation proves a universal statement;
- that any formal skeleton is complete;
- that any Clay problem is solved;
- that any publication, prize or revenue will result.

The first externally meaningful promotion requires a sourced real problem,
current literature review, a nontrivial mathematical result, independent
reproduction and appropriate expert review.
