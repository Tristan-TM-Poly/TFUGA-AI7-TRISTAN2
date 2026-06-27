# Omega AUTO2 Card Contract

Every generated card must contain these fields:

- `index`: integer from 1 to 1024
- `domain`: Omega domain name
- `sector`: sector name
- `atom`: one of the 16 generation atoms
- `slug`: deterministic lowercase identifier ending in `_v1`
- `priority`: `P0`, `P1`, `P2`, `P3_STEALTH_IP`, or `P4_RESEARCH`
- `score`: E-cap score from 0 to 100
- `state`: card state machine value
- `human_review`: boolean review lock
- `disclosure_level`: `public`, `internal`, `trade_secret`, `patent_review`, or `never_publish_raw`
- `oak_status`: OAK status
- `proof_rule`: proof or safety condition
- `revenue_role`: economic role
- `depends_on`: card dependency list
- `labels`: GitHub label list

## State machine

```text
IDEA -> DRAFTED -> ISSUE_READY -> ISSUE_OPENED -> BRANCH_READY -> PR_READY -> CI_PASS -> OAK_PASS -> HUMAN_REVIEW -> MERGE_READY -> MERGED
```

A failed or unsafe card goes to:

```text
ARCHIVED_M_MINUS
```

## Hard rules

- No `MERGE_READY` without CI pass and OAK pass.
- No public ECC disclosure without IP review.
- No pricing meter without human review.
- No regulated-domain claim without human review.
- Every executable card must include a failure-mode or M-minus note.
