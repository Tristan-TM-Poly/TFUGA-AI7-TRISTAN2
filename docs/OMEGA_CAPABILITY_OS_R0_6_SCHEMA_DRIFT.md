# Ω-CAPABILITY-OS-T∞ R0.6 — Connector Schema Drift Laboratory

## Status

R0.6 adds a deterministic compatibility/falsification layer around the R0.5
provider-response normalizers.

It does **not** invoke providers, widen permissions, or convert a fixture into evidence
about the external world. Its job is narrower:

```text
sanitized connector fixture
→ deterministic schema mutations
→ R0.5 normalizer
→ normalized receipt / rejection
→ expected-vs-observed classification
→ compatibility matrix
→ M− candidates
```

The R0.6 OAK question is:

> Does the normalizer behave as declared when the connector response shape changes?

It is not:

> Is the provider correct, complete, secure or semantically truthful?

## Why this layer exists

R0.5 closed the raw-response → typed-receipt gap, but a static unit test can still give
false confidence if a connector changes its response shape later.

Provider drift can be:

- additive: a new field appears;
- envelope drift: `result`, `content` or `structuredContent` changes;
- identity drift: response metadata points to a different connector/action;
- omission drift: a required output disappears;
- type drift: an object becomes a list or scalar;
- semantic drift: the selected value changes while the path still exists;
- freshness drift: a candidate SHA changes;
- error drift: a nominal result becomes a provider failure.

R0.6 makes these cases executable and measurable.

## Fixture provenance classes

Every fixture must declare one of two source kinds.

### `captured_sanitized`

A real connector interaction was observed, but only a minimum public-safe response
shape is retained. Private payloads and live identifiers are replaced.

Current R0.6 captured/sanitized fixture families:

1. GitHub PR metadata;
2. ChatGPT Files/Library search;
3. Google Drive metadata search.

The GitHub fixture has the strongest fidelity because the connector returned a
structured PR object directly.

Files/Library and Drive are labeled more conservatively as
`live_rendered_shape_reconstructed_and_sanitized`: the visible connector response was
used to derive the fixture shape, but the fixture is not represented as a byte-for-byte
raw API capture.

### `contract_synthetic`

No live user data was captured. The fixture exists only to test the declared adapter
contract.

Current synthetic families:

- Gmail;
- Google Calendar;
- Web.

Synthetic fixtures are useful tests, but they must never be counted as live provider
validation.

## Privacy boundary

The committed fixture corpus declares:

```json
{
  "raw_private_content_committed": false,
  "real_user_identifiers_committed": false,
  "real_message_or_event_ids_committed": false
}
```

The corpus intentionally uses inert values such as:

```text
file_fixture_r06
drive_fixture_r06
message_fixture_r06
event_fixture_r06
https://*.invalid/...
```

No mailbox body, calendar content, private ChatGPT transcript, live Drive identifier,
private Library identifier or private connector URL is required by the benchmark.

## Drift expectations

Each generated case carries an expectation.

### `SURVIVE`

Benign compatibility drift must preserve the baseline normalized receipt signature.

Examples:

- additive unknown metadata;
- omitted optional connector/action identity metadata;
- JSON `result` envelope;
- `structuredContent` envelope;
- JSON `content` envelope;
- nested `result → structuredContent`;
- second-order additive metadata.

### `REJECT`

The normalizer must fail closed.

Examples:

- connector identity mismatch;
- action identity mismatch;
- required output removed;
- stale candidate SHA.

### `FAILURE_RECEIPT`

A connector/provider error must become a typed `ExternalActionReceipt(status=FAILURE)`,
rather than fake success or an unstructured exception.

### `DETECT`

Some changes can still produce a structurally valid receipt under R0.5, but they must
not be silently counted as compatible.

`DETECT` accepts either:

```text
DEGRADED
or
REJECT
```

Examples:

- required output becomes null;
- output JSON type changes;
- selected output value changes semantically.

`DEGRADED` means normalization completed but the normalized receipt signature differs
from the baseline signature.

This distinction is important:

```text
normalizer accepted response
!=
response remained semantically compatible
```

## Deterministic mutation court

For every fixture, R0.6 generates:

- one baseline;
- three additive-metadata cases;
- one identity-omission case;
- four envelope/wrapper variants;
- connector mismatch;
- action mismatch;
- provider error;
- missing required output;
- null required output;
- wrong-type required output;
- semantic output change;
- three deterministic second-order additive cases;
- candidate-SHA stale case where applicable.

Current deterministic corpus size:

```text
GitHub: 20 cases
Files: 19
Drive: 19
Gmail: 19
Calendar: 19
Web: 19
----------------
Total: 115 cases
```

No randomness is used. The same fixture corpus must produce the same report.

## Compatibility metrics

R0.6 reports two different concepts.

### Classification accuracy

Did the court behave according to the declared expectation?

```text
classification_accuracy
=
correct expected classifications / total cases
```

This is the primary OAK gate for the drift harness itself.

### Breaking detection rate

For cases expected to be `REJECT` or `DETECT`:

```text
breaking_detection_rate
=
cases observed as REJECT or DEGRADED
/
breaking cases
```

This prevents a structurally successful but changed receipt from being counted as
full compatibility.

## Provider matrix

The corpus report groups results by provider:

```text
provider
→ fixture count
→ case count
→ correct classifications
→ mismatches
→ breaking cases
→ breaking detected
→ classification accuracy
→ breaking detection rate
```

The matrix is intended to become version-indexed as real connector fixtures accumulate.

## M− candidates

Detected breaking drift is emitted as:

```text
schema_drift_observation
→ M_MINUS_CANDIDATE
```

This is deliberately a *candidate*, not a claim that an actual production incident
occurred.

A future real connector failure can be linked to the matching mutation family without
rewriting historical results.

## Executable interface

Run the full corpus with:

```bash
python -m omega_capability_os_t.drift \
  examples/capability_os_r06_fixture_corpus.json
```

The command prints a deterministic JSON report and exits non-zero if any classification
expectation is violated.

The normal pytest suite also exercises the full 115-case corpus.

## Fail-closed properties

R0.6 verifies that:

```text
wrong connector identity → REJECT
wrong action identity → REJECT
missing required output → REJECT
stale candidate SHA → REJECT
provider failure → FAILURE receipt
null/type/value change → DEGRADED or REJECT
benign additive/wrapper drift → exact signature SURVIVE
```

## OAK boundaries

R0.6 PASS means:

- the fixture corpus is parseable;
- fixture provenance class is explicit;
- generated mutations are deterministic;
- expected drift classifications match observed R0.5 behavior;
- known breaking mutations are detected;
- committed fixtures respect the declared sanitization boundary.

R0.6 PASS does **not** mean:

```text
all future provider schemas are supported
synthetic Gmail fixture == live Gmail validation
synthetic Calendar fixture == live Calendar validation
synthetic Web fixture == live Web validation
rendered Files fixture == exact raw provider response
rendered Drive fixture == exact raw provider response
schema compatibility == semantic truth
matching normalized receipt == external action really occurred
CI green == provider contract is permanently stable
```

## Promotion rule

A future connector schema/version should not be marked compatible only because one
happy-path fixture normalizes.

Preferred promotion rule:

```text
new sanitized capture
→ add provider/version fingerprint
→ run deterministic R0.6 mutation court
→ classification_accuracy == 1
→ breaking_detection_rate == 1
→ inspect M− candidates
→ then widen compatibility claim
```

## Next bounded frontier — R0.7

R0.7 should move from hand-authored fixture contracts to a controlled schema-profile
miner:

```text
authorized sanitized connector captures
→ structural schema fingerprint
→ version/profile clustering
→ selector stability map
→ automatic candidate contract
→ R0.6 mutation court
→ human/OAK review
→ promoted provider profile
```

Important constraint: R0.7 must mine *structure*, not persist private content.

The objective is an adaptive compatibility layer that learns provider schema versions
without learning or publishing the user's mailbox, calendar, Drive contents, private
ChatGPT memory or other sensitive payloads.
