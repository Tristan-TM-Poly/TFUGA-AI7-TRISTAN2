# Ω-CAPABILITY-OS-T∞ — Capability Fabric R0.3

Status: **prototype executable / external-adapter contract / OAK-bounded / non-autonomous**

Ω-CAPABILITY-OS-T∞ sits below `Ω-INTENT-TO-EVERYTHING`.
The intent layer decides **what work should exist**. Capability OS decides **which
available capability chain should be used**, how failures fall back, what external
action is still required, and what evidence is strong enough to continue.

## Canonical loop

```text
Intent
  -> WorkUnit
  -> Capability Intent
  -> Capability Genome
  -> health/VOI planner
  -> local handler OR external adapter request
  -> normalized receipt
  -> resume
  -> EvidenceReceipt
  -> OAK
  -> M+ / M-
  -> updated capability health
```

R0.3 adds the missing boundary between the Python planner/runtime and actual ChatGPT
connectors/tools. **The package still never calls remote tools by itself.** It emits a
normalized request that an authorized execution layer can invoke through GitHub,
Files, Drive, Gmail, Calendar, Web, or another connector, then validates the returned
receipt before resuming.

## R0.1 — Capability Genome

Each capability declares domains, consumed/produced tokens, authority, quality,
information gain, verifiability, reuse, cost, latency, risk, alternatives and known
failure modes.

Authority is explicit:

- `read` and `draft` may be planned by default;
- `write` requires `allow_mutation=true`;
- `irreversible` requires both `allow_mutation=true` and `allow_irreversible=true`.

Planning permission is **not** execution authorization.

The first live benchmark came from PR #415: a generic log route returned empty
content, while the specialized GitHub Actions job-log path exposed `No module named
pytest`. That failure is retained as M- and the fallback path is a permanent regression
case.

## R0.2 — WorkUnit bridge and bounded runtime

`omega_intent_t.models.WorkUnit` is used as the execution IR rather than replaced:

```text
WorkUnit
  -> dependency evidence tokens
  -> generator capability
  -> artifact tokens
  -> validation capabilities
  -> validation tokens
  -> Capability plan
```

`CapabilityRuntime` executes only explicitly registered handlers. Missing handlers
produce `ACTION_REQUIRED`, never fake success. Runtime outputs include observations,
sources, output fingerprints, M+/M- records and learned health.

A runtime OAK PASS requires:

```text
plan == READY
AND all required outputs exist
AND no action remains pending
AND candidate_sha == evidence_sha
```

## R0.3 — External Execution Adapters

### ExternalBinding

A binding maps one Capability Genome node to one external connector action.

Example:

```json
{
  "capability_id": "github.fetch_pr",
  "connector": "GitHub",
  "action": "fetch_pr",
  "argument_template": {
    "repo_full_name": "$repo",
    "pr_number": "$pr_number"
  }
}
```

Template references are validated against the capability's declared inputs. Unknown
input tokens fail validation before execution.

The repository ships concrete binding descriptions for the currently modeled read
paths:

- GitHub PR metadata and PR diff;
- ChatGPT Files semantic search;
- Google Drive search;
- Gmail message-ID search;
- Google Calendar bounded event search;
- Web search.

These bindings describe invocation shape. They do not grant OAuth scope, connector
availability, user consent, or write permission.

### ExternalActionRequest

When CapabilityRuntime reaches a capability without a local handler, an
`ExternalResolver` converts the step into a deterministic request.

The audit form contains:

```text
request_id
capability_id
connector
action
authority
expected_outputs
candidate_sha
plan_fingerprint
arguments_fingerprint
```

Raw arguments are **redacted by default**. `execution_payload()` or
`pending_requests(include_arguments=True)` must be requested explicitly by the
execution layer.

This separation is important for Gmail, Drive, Files and other contexts where request
arguments may contain private search terms or identifiers.

### ExternalActionReceipt

The execution layer normalizes a real connector result into:

```text
request_id
capability_id
connector
action
status = SUCCESS | FAILURE | DEGRADED
outputs
sources
notes
error
observed_candidate_sha
```

A SUCCESS receipt is rejected unless it:

1. matches the deterministic request ID;
2. matches capability, connector and action;
3. contains every output declared by the capability;
4. does not contradict an explicitly observed candidate SHA.

Outputs are also redacted by default in audit serialization and represented by a
stable fingerprint.

## Suspend -> external action -> resume

R0.3 supports a deterministic two-pass pattern:

```text
pass 1
  CapabilityRuntime
  -> ExternalResolver
  -> ACTION_REQUIRED + redacted request

external execution layer
  -> invoke authorized connector
  -> normalize result as ExternalActionReceipt

pass 2
  same intent + same inputs + receipt
  -> request_id reproduced
  -> receipt validated
  -> output injected into runtime state
  -> remaining plan continues
```

The request ID depends on capability, connector/action, argument fingerprint,
candidate SHA and optional plan fingerprint, so changed inputs or changed candidate
state invalidate the old receipt instead of silently reusing it.

## Fallback semantics

If an external receipt reports failure, CapabilityRuntime records M- and may use a
fallback only when that fallback:

- is explicitly declared;
- is not health `FAIL`;
- preserves the outputs required by the failed capability;
- has all runtime inputs;
- respects the intent's authority gates.

A `write` fallback therefore cannot silently replace a failed `read` operation when
mutation is not authorized.

If the fallback itself is external and has no receipt yet, runtime emits a normalized
external request for that fallback rather than recording a fabricated failure.

## CLI

```bash
python -m omega_capability_os_t describe examples/capability_os_registry.json

python -m omega_capability_os_t workunit-plan \
  examples/capability_os_workunit.json \
  --completed-dependency WU-PREV

python -m omega_capability_os_t external-run \
  examples/capability_os_registry.json \
  examples/capability_os_external_intent.json \
  examples/capability_os_external_bindings.json \
  --values examples/capability_os_external_values.json \
  --candidate-sha <SHA> \
  --evidence-sha <SHA>
```

Without an external receipt the command exits non-zero with OAK `HOLD` and a redacted
request. `--include-arguments` exposes the execution payload intentionally. A later run
may provide `--receipts <json>` to resume.

## Evidence boundaries

R0.3 can certify only the following narrow properties:

- deterministic capability selection;
- binding schema consistency;
- authority gating inside the planner;
- receipt/request identity consistency;
- declared output presence;
- runtime completion;
- candidate/evidence SHA freshness;
- M+/M- health derivation from recorded outcomes.

It does **not** certify semantic truth, scientific truth, legal permission, external
provider correctness, consent, or that a proposed write/merge/send/delete should occur.
Those remain separate gates.

## Next convergence

R0.4 should add **connector-specific receipt normalizers and a ChatGPT execution
bridge**: real connector response -> normalized outputs/sources -> receipt -> resumed
CapabilityRuntime, with schema tests for GitHub, Files, Drive, Gmail, Calendar and Web.
That layer should remain read-first and require explicit authorization for every
mutation class.
