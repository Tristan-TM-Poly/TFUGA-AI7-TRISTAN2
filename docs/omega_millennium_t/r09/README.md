# Ω-PROBLEM-ATLAS-T∞ R0.9

## Publication, Novelty, Prize and IP Gate

R0.9 is the fail-closed boundary between a research artifact and any proposed
publication, submission, competition entry, prize statement, patent filing,
open-source release or public presentation.

It compiles an auditable **dry-run bundle**. It does not perform the external
action.

```text
research artifact
  -> exact statement and assumptions
  -> evidence references
  -> independent attestations
  -> novelty / prior-art / reproducibility / IP checks
  -> signed receipt
  -> fail-closed decision
  -> human review only
```

## Non-negotiable invariant

```text
repository status != publication
CI status         != theorem correctness
model output       != novelty approval
open PR            != prize eligibility
```

R0.9 never infers:

- mathematical truth;
- proof correctness;
- novelty;
- patentability;
- journal acceptance;
- competition eligibility;
- prize recognition;
- Clay Mathematics Institute recognition;
- solution of an open problem.

## Commands

```bash
omega-problem-promotion compile \
  --bundle-json promotion/request.json \
  --output-dir generated/promotion_r09

omega-problem-promotion audit generated/promotion_r09
```

The compiler has no `submit`, `publish`, `file`, `release`, `send` or `claim`
command.

## Supported statuses

- `experiment`;
- `restricted_theorem`;
- `manuscript`;
- `formal_artifact`;
- `independently_reviewed_result`.

These are artifact classes. They are not automatically claims of truth.

## Supported destinations

- `internal_archive`;
- `public_preprint`;
- `journal_submission`;
- `competition_submission`;
- `prize_claim`;
- `patent_filing`;
- `open_source_release`;
- `public_talk`.

The destination determines additional mandatory checks. A destination only
expresses the proposed next action; R0.9 does not perform that action.

## IP decisions

Every request must choose exactly one current IP route:

- `publish`;
- `patent`;
- `secret`;
- `open_source`;
- `abandon`.

Contradictory combinations fail closed. Examples:

- `secret -> public_preprint` is blocked;
- `abandon -> public_talk` is blocked;
- `publish -> patent_filing` is blocked;
- `patent -> patent_filing` may proceed to human review;
- `open_source -> open_source_release` may proceed to human review.

A passed gate does not determine legal patentability and is not legal advice.

## Check families

R0.9 recognizes eighteen typed check families:

1. exact statement and scope;
2. dated literature search;
3. prior-art search;
4. novelty comparison;
5. independent reconstruction;
6. reproducibility snapshot;
7. proof dependency audit;
8. hidden-assumption audit;
9. formal-verification status;
10. negative-results and M-minus coverage;
11. authorship;
12. license and copyright;
13. dataset terms;
14. competition rules;
15. official prize recognition;
16. IP decision;
17. limitations;
18. citations.

Mandatory checks are the union of requirements for the requested artifact
status and destination.

A mandatory check must have at least one `pass` attestation. `fail` always
blocks. `not_applicable` cannot satisfy a mandatory requirement.

## Independent review

The following checks require an independent reviewer:

- novelty review;
- independent reconstruction;
- dependency audit;
- hidden-assumption audit.

The reviewer cannot be an author and cannot use a role such as `model`,
`generator`, `assistant`, `author`, `coauthor` or `owner`.

A generated text cannot approve itself. The input parser recursively rejects
self-approval fields including:

- `approved`;
- `gate_passed`;
- `novel`;
- `correct`;
- `proof_verified`;
- `publication_authorized`;
- `submission_authorized`;
- `prize_eligible`;
- `prize_winner`;
- `clay_recognized`;
- `truth_probability`;
- `confidence_probability`.

## Evidence references

Every attestation must reference one or more evidence records. Each record
contains:

- stable reference ID;
- source URI;
- SHA-256 source digest;
- timezone-aware observation date;
- exact source location;
- license note;
- optional metadata.

A citation or mention is not automatically support. The reviewer attests only
to the scope stated in the check.

## Literature and prior-art searches

A passing search attestation requires:

- search queries;
- databases or indexes searched;
- source count;
- explicit search cutoff date;
- evidence references preserving the result set or report.

A search can report that no conflict was found. It cannot prove universal
novelty.

## Reproducibility

A reproducibility snapshot records:

- code digest;
- data digest or explicit no-data marker;
- environment digest;
- replay command.

An independent reconstruction records its own environment and replay command.
A `partial` or `failed` reconstruction cannot be labeled `pass`.

## Formal artifacts

For status `formal_artifact`, the formal-verification attestation must state:

- checker;
- checker version;
- `kernel_checked: true`.

This records the supplied verifier receipt. R0.9 does not execute Lean, Coq,
Isabelle or another proof assistant itself.

## Negative memory

The publication bundle always carries the supplied M-minus history. The
negative-results attestation declares the exact number of included records.
A mismatch blocks the gate.

This prevents a polished manuscript from silently dropping failed methods,
counterexamples or known limitations.

## Prize claims

`prize_claim` is the strictest destination.

It requires:

- artifact status `independently_reviewed_result`;
- official competition rules;
- confirmed eligibility;
- official-authority reviewer role;
- official authority evidence;
- `official_award_status: awarded`.

A nomination, submission, repository badge, viral post, accepted preprint or
successful CI run is not an award.

Even when these fixture checks pass, R0.9 sets:

```json
{
  "prize_claim_submitted": false,
  "prize_or_clay_recognition_inferred": false
}
```

## Signatures

The signature payload binds:

- request identity;
- canonical problem and artifact IDs;
- exact statement and assumptions;
- status and destination;
- authors;
- IP decision;
- evidence digests;
- check digests;
- M-minus digest.

At least one non-author independent gate signature is required.

Public destinations additionally require:

- an authenticated `pgp` or `sigstore` gate signature;
- an `ip_reviewer` signature.

`sha256_detached` is supported only as a deterministic internal fixture. It is
not identity authentication and is blocked for public destinations.

## Materialized output

R0.9 writes:

- `request.json`;
- `checklist.jsonl`;
- `promotion_receipt.json`;
- `publication_bundle.json`;
- `SUMMARY.md`;
- `manifest.json`;
- `report.json`.

The report is path-normalized, so equivalent compilations in different output
directories are byte-identical.

## Audit

The audit:

1. validates and reloads the request;
2. recomputes every checklist row;
3. recomputes every blocker;
4. recomputes the signature payload;
5. reconstructs the promotion receipt;
6. reconstructs the publication bundle;
7. reconstructs the human summary;
8. verifies every file digest;
9. verifies manifest, bundle, receipt and report digests;
10. rejects any external-action or scientific-claim flag.

Stored gate decisions are never trusted.

## Gate meaning

`gate_ready: true` means only:

> The supplied fixture satisfies the machine-readable R0.9 policy and is ready
> for a separate human decision.

It does not mean:

- publish now;
- submit now;
- disclose now;
- patent now;
- claim a theorem;
- claim a prize;
- claim an open problem is solved.

## OAK status

`CERTIFIED_PROMOTION_GATE_FIXTURE_R0_9` certifies deterministic software
behavior for supplied fixtures after tests and audit succeed.

It does not certify external facts, legal conclusions, mathematical truth,
novelty, correctness, acceptance, eligibility, recognition or solution of any
problem.
