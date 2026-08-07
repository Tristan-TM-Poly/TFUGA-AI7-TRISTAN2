# Ω-WEB-HG-T∞ R0.5 — Policy Compiler MAX

## Purpose

R0.5 converts policy evidence into deterministic technical constraints before a
Web adapter may request, normalize or retain data.

```text
policy evidence
→ typed PolicyProfile
→ deterministic compiler
→ review state
→ CompiledPolicy
→ request gate
→ record gate
→ storage gate
→ append-only registry
→ OAK report
```

The compiler is not legal advice and does not create permission. It makes the
currently represented interpretation explicit, testable, versioned and
fail-closed.

```text
POLICY_DOCUMENT != EXECUTABLE_PERMISSION
COMPILED_POLICY != LEGAL_ADVICE
PUBLIC_ACCESS != REPUBLICATION_PERMISSION
TECHNICAL_PASS != PERMANENT_AUTHORIZATION
```

## Core artifacts

```text
omega_web_hg_t/r05/models.py
omega_web_hg_t/r05/policy_compiler.py
omega_web_hg_t/r05/policy_gate.py
omega_web_hg_t/r05/registry.py
schemas/omega_web_hg_policy_profile_v1.schema.json
schemas/omega_web_hg_compiled_policy_v1.schema.json
tests/test_omega_web_hg_r05_policy.py
```

## Profile model

A profile records:

- source identifier and policy URL;
- observation and review dates;
- epistemic status of the interpretation;
- explicitly allowed routes;
- allowed and forbidden content classes;
- field allowlist and denylist;
- required environment variables;
- request rate, burst and Retry-After behavior;
- User-Agent and contact identity rules;
- retention and encryption rules;
- attribution requirements;
- jurisdiction and notes;
- enforcement mode.

A profile receives a stable SHA-256 digest over canonical JSON.

## Review states

Input evidence status:

```text
verified
inferred
ambiguous
expired
human_review_required
```

Compiled execution status:

```text
pass
human_review
fail
```

An inferred, ambiguous, expired or overdue policy never silently becomes a
network permission. Requests and storage are denied until the profile is
reviewed.

## Runtime gates

### Request gate

Checks:

- policy is executable;
- route is explicitly allowed;
- descriptive User-Agent exists when required;
- contact email mode is respected;
- required environment variables are present;
- requested rate is positive;
- recommended and maximum rates are enforced.

### Record gate

Checks every nested key with normalized aliases. Examples considered equivalent
for policy matching include:

```text
full_text
fullText
full-text
fulltext
```

R0.5 blocks at least:

```text
abstract
body
content
explanation
full_text
pdf
raw_body
raw_response
complete author payloads
```

Default enforcement is `reject`. An explicit `redact` mode may produce a
sanitized object, but every removal remains represented as a warning in the
content-addressed decision.

### Storage gate

Evaluates:

- content class;
- target storage level 0–3;
- retention mode;
- maximum retention period;
- encryption requirements;
- policy review state.

Raw HTTP responses are forbidden by every initial profile. Normalized metadata
may be retained at level 1. Level 3 requires encryption at rest.

## Evidence registry

`PolicyRegistry` uses SQLite/WAL and records four deduplicated object families:

```text
profiles
compiled_policies
gate_decisions
storage_decisions
```

Denied actions are preserved as negative memory rather than discarded.
Deterministic JSONL export produces a registry manifest that states:

```text
raw_policy_documents_persisted = false
compiled_rules_are_legal_advice = false
denied_actions_preserved = true
```

## Initial governed catalog

R0.5 includes technical snapshots for:

1. Wikimedia;
2. Crossref;
3. PubMed;
4. PMC OAI;
5. NIST PDR;
6. NASA Open APIs;
7. CERN Open Data;
8. USGS;
9. ESA CCI;
10. Government of Canada Open Data;
11. OpenAlex;
12. arXiv.

At the initial 2026-08-03 evaluation date, eleven profiles compile to `pass`.
arXiv remains `human_review` and cannot execute.

## CLI

```bash
omega-web-hg-r05 catalog --as-of 2026-08-03
omega-web-hg-r05 compile crossref --as-of 2026-08-03
omega-web-hg-r05 audit --as-of 2026-08-03
```

Materialize all evidence:

```bash
omega-web-hg-r05 materialize \
  --as-of 2026-08-03 \
  --output-dir generated/omega_web_hg_r05
```

Gate a request:

```bash
omega-web-hg-r05 gate-request openalex rest_api \
  --as-of 2026-08-03 \
  --rps 1 \
  --env OPENALEX_API_KEY=present
```

Gate an object:

```bash
omega-web-hg-r05 gate-record crossref record.json \
  --as-of 2026-08-03
```

Compare two policy snapshots:

```bash
omega-web-hg-r05 drift old-profile.json new-profile.json \
  --as-of 2026-08-03
```

The drift command exits nonzero when a change requires human review. Risk flags
include:

```text
forbidden_fields_relaxed
new_routes_enabled
environment_requirement_relaxed
raw_response_retention_relaxed
review_status_degraded
```

## OAKBench

The focused suite verifies:

- twelve governed profiles;
- deterministic compilation;
- expiration and overdue review behavior;
- route allowlisting;
- User-Agent rules;
- environment-key fail-closed behavior;
- maximum request rates;
- nested and camelCase forbidden-field detection;
- explicit redaction;
- field allowlisting;
- attribution requirements;
- raw-response storage denial;
- encryption for level 3;
- policy-relaxation drift detection;
- SQLite deduplication and JSONL export;
- CLI audit and materialization.

The decisive invariant is executable:

> A profile forbidding full text prevents persistence of `abstract`, `body` or
> `full_text`, including nested and aliased forms.

## Integration path

R0.5 is designed to sit in front of R0.4:

```text
R0.4 Adapter
→ R0.5 request authorization
→ fetch
→ R0.4 parser
→ R0.5 record gate
→ R0.5 storage decision
→ R0.4 receipts / M-minus / Merkle
```

The next integration should make every R0.4 adapter receive a compiled policy
digest and refuse execution when its policy is missing, stale or incompatible.

## Remaining boundaries

R0.5 does not yet:

- parse arbitrary legal prose automatically;
- decide whether a policy is legally sufficient;
- store WARC or full text;
- repair adapters autonomously;
- infer permission from robots.txt;
- prove source truthfulness;
- provide complete jurisdictional compliance.

Those remain separate research and product gates.
