# Ω-CAPABILITY-OS-T∞ R0.5 — Provider Response Normalizers

## Status

R0.5 adds the missing execution-boundary adapter between a **real connector result** and the already-existing `ExternalActionReceipt` contract.

It does **not** add another planner and it does **not** invoke providers itself.

```text
Intent / WorkUnit
→ Capability plan
→ ExternalActionRequest
→ separately authorized provider invocation
→ raw provider response
→ R0.5 provider normalizer
→ validated ExternalActionReceipt
→ ExternalResolver resume
→ OAK / M+ / M−
```

## Why R0.5 exists

R0.3 introduced deterministic external handoff and R0.4 separated capability authority from real provider side effects. One gap remained:

> a raw connector response is not yet a typed proof that the requested capability actually produced the declared outputs for the expected state.

R0.5 closes that gap with explicit provider-normalization contracts.

## Provider family

The package exposes:

- `normalize_github_response`
- `normalize_files_response`
- `normalize_drive_response`
- `normalize_gmail_response`
- `normalize_calendar_response`
- `normalize_web_response`
- generic `normalize_provider_response`

These functions convert a provider-specific raw response into a receipt only after structural and semantic gates pass.

## ResponseContract

A contract binds each declared capability output to one or more deterministic selectors in the provider response.

```python
ResponseContract(
    provider="github",
    output_paths={
        "pr_metadata": "pull_request",
        "commit_sha": "pull_request.head_sha",
    },
    candidate_sha_paths=("pull_request.head_sha", "head_sha", "sha"),
    source_paths=("url", "html_url"),
)
```

Selectors use deterministic dotted paths. Lists can be indexed numerically.

Ordered fallback selectors are supported:

```python
{
    "commit_sha": (
        "pull_request.head_sha",
        "commit.sha",
        "sha",
    )
}
```

The first present value wins.

## Exact-output invariant

The normalizer contract must map:

```text
exactly every request.expected_outputs
and no undeclared output name
```

Therefore:

```text
provider returned something useful
!=
capability produced its declared outputs
```

A nominally successful raw response missing even one required output fails closed.

## Provider binding invariant

A GitHub request cannot be normalized by the Gmail normalizer, a Files request cannot be normalized as Web, etc.

Connector names are canonicalized only enough to recognize known aliases such as:

```text
Google_Drive    → googledrive
Google_Calendar → googlecalendar
```

This alias normalization is not permission widening.

## Envelope identity

When a real connector response exposes identity metadata such as:

```text
connector_name
action_name
```

R0.5 verifies it against the original `ExternalActionRequest`.

A contradictory provider/action identity fails closed.

R0.5 does not fabricate identity metadata when a provider does not expose it.

## GitHub exact-SHA freshness

Candidate-bound GitHub requests receive a stronger default rule:

```text
request.candidate_sha exists
→ normalized SUCCESS must contain observed_candidate_sha
→ observed_candidate_sha == request.candidate_sha
```

This prevents:

```text
PR state read at SHA A
→ branch moves to SHA B
→ stale result silently promoted as evidence for B
```

The existing runtime still separately requires candidate SHA == evidence SHA for final OAK PASS.

So the chain becomes:

```text
raw provider state SHA
== request candidate SHA
== runtime evidence SHA
```

within the boundaries of the data actually returned by the provider.

## Side-effect attestation remains R0.4-governed

R0.5 reuses, rather than bypasses, the R0.4 mutation contract.

For a successful request whose external authority is `write` or `irreversible`:

```text
mutation_performed == true
```

is required.

For `read` or `draft` requests:

```text
mutation_performed == true
```

is rejected.

Provider response normalization therefore cannot turn a read request into a write receipt.

## Failure normalization

A connector-level failure is not interpreted as malformed success.

Known error envelopes are converted to:

```text
ExternalActionReceipt(
    status="FAILURE",
    outputs={},
    error=...
)
```

This is important because the existing runtime can then:

```text
provider FAILURE receipt
→ M−
→ explicit authority-preserving fallback
→ recovery or terminal failure
```

rather than losing the provider failure outside the execution graph.

## Raw-response privacy boundary

R0.5 computes:

```text
raw_response_fingerprint = stable_digest(raw_response)
```

and stores that fingerprint as receipt metadata.

By default it does **not** copy the raw provider payload into the receipt.

This supports:

- replay/audit correlation;
- duplicate detection;
- provider-result identity checking;
- reduced accidental persistence of mailbox bodies, Drive contents, private Library data or other sensitive payloads.

The fingerprint is not semantic proof that the response is correct.

## Provider wrappers

### GitHub

Default freshness selectors:

```text
pull_request.head_sha
head_sha
commit.sha
sha
```

Default source selectors:

```text
url
html_url
display_url
```

### Files / ChatGPT Library

Supports structured connector envelopes and JSON-encoded `content` bodies while keeping the raw body outside the receipt by default.

Typical use:

```text
Library search/fetch
→ normalize_files_response
→ typed memory-pointer/context receipt
```

### Google Drive

Typical use:

```text
Drive search/fetch/create/update
→ normalize_drive_response
→ file/object receipt
```

Mutating Drive actions still require explicit mutation attestation.

### Gmail

Typical use:

```text
Gmail read/search/draft/send/label action
→ normalize_gmail_response
→ typed message/thread/action receipt
```

A successful send or persistent label mutation is a write, regardless of provider naming.

### Google Calendar

Typical use:

```text
Calendar read/free-busy/create/update/delete/respond
→ normalize_calendar_response
→ typed event/schedule receipt
```

### Web

Typical use:

```text
web search/open/finance/weather/etc.
→ normalize_web_response
→ typed observation receipt
```

The Web normalizer is read-only in R0.5.

## Adversarial courts

R0.5 adds tests for:

1. exact GitHub SHA-bound success;
2. stale GitHub SHA rejection;
3. missing observed SHA rejection;
4. misbound connector rejection;
5. misbound action rejection;
6. successful response missing declared output;
7. provider error → typed FAILURE receipt;
8. JSON-content Files/Library unwrapping;
9. Drive normalization;
10. Gmail normalization;
11. Calendar normalization;
12. Web list-index selectors;
13. write success without mutation attestation;
14. read receipt claiming mutation;
15. undeclared output mapping;
16. ordered selector fallbacks;
17. raw-response fingerprinting without raw-body receipt persistence.

## OAK boundaries

R0.5 strengthens the evidence pipeline, but the following remain distinct:

```text
raw response received
!= provider result belongs to intended action unless identity is established

normalized receipt
!= provider implementation independently verified

provider SUCCESS
!= required outputs present

required outputs present
!= semantically correct outputs

matching SHA
!= scientific truth

mutation_performed=true
!= independent proof of provider mutation

raw-response fingerprint
!= correctness

CI green
!= external-world validation
```

## ChatMem integration target

R0.5 enables the next executable ChatMem path:

```text
Library pointer fetch
→ normalize_files_response
→ bootstrap receipt

Library checkpoint persistence
→ normalize_files_response(mutation_performed=true)
→ library_persistence_receipt

GitHub checkpoint write
→ normalize_github_response(mutation_performed=true)
→ github_checkpoint_receipt

both receipts
→ pointer update request
→ normalized pointer mutation receipt
```

The pre-existing ChatMem privacy/OAK gate remains mandatory before those writes are even requested.

## Next frontier — R0.6

The next bounded improvement should measure **receipt fidelity against captured real connector fixtures** rather than expanding abstraction depth.

Candidate work:

```text
sanitized real connector fixtures
→ schema-drift corpus
→ property/adversarial tests
→ provider version fingerprints
→ normalizer confidence / degradation states
→ compatibility matrix
```

The objective is to detect connector schema drift before it silently degrades evidence quality.
