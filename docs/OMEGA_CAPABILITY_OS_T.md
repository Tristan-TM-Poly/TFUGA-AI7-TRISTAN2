# Ω-CAPABILITY-OS-T∞ — Capability Fabric R0.2

Status: **prototype executable / WorkUnit bridge / bounded runtime / non-autonomous**

Ω-CAPABILITY-OS-T∞ is the capability-selection, execution-receipt and evidence layer
below `Ω-INTENT-TO-EVERYTHING`.

The upstream intent system decides **what work should exist**. Capability OS decides
**which capability chain can realize it**, whether the chain is currently healthy and
authorized, what actually executed, and whether the evidence is fresh enough for a
bounded OAK result.

## R0.2 convergence

R0.2 closes the largest R0.1 gap:

```text
omega_intent_t.WorkUnit
  -> Capability Intent
  -> capability plan
  -> registered handler runtime
  -> execution observations
  -> M+ / M-
  -> learned health
  -> exact-SHA EvidenceReceipt
  -> OAK
```

This is intentionally not a second intent planner. `omega_intent_t` keeps ownership of
requirements, work-unit decomposition and dependency topology.

## 1. WorkUnit bridge

`compile_workunit()` converts an existing `WorkUnit` into:

- a spec token containing the serialized work unit;
- dependency-completion tokens;
- artifact tokens for every declared output path;
- validation tokens for every declared validation;
- one synthetic generation capability;
- one validation capability per validation;
- a Capability OS `Intent`.

If a required upstream work unit is not listed as completed, its dependency token is
absent and the plan is `HOLD`.

### Authority mapping

Default generation authority is deliberately conservative:

| WorkUnit risk | Capability authority |
| --- | --- |
| `low`, `normal`, `ip_sensitive` | `draft` |
| `elevated`, `public` | `write` |
| `irreversible` | `irreversible` |

Thus an elevated work unit cannot become executable merely because it was planned
upstream. `allow_mutation=true` is still required; irreversible work additionally
requires `allow_irreversible=true`.

## 2. Bounded runtime

`CapabilityRuntime` executes only registered handlers.

A handler receives:

```text
(capability, consumed_token_values)
```

and must return either a token mapping or `HandlerResult`.

The runtime verifies that all outputs declared by the capability are actually returned.
Missing outputs are failures, not partial successes.

If no handler exists, execution stops with:

```text
ACTION_REQUIRED
```

This matters for ChatGPT connectors and external tools: the Python package does not
pretend it can call a connector that has not been explicitly bridged into the runtime.

## 3. Safe fallback execution

When a handler fails, R0.2 can try a declared alternative only if the fallback:

1. exists in the same registry;
2. is not health=`FAIL`;
3. is allowed by the current authority policy;
4. can produce every output required from the failed capability;
5. has all runtime inputs available.

Eligible fallbacks are ranked by health-adjusted utility.

This blocks the unsafe pattern:

```text
read capability fails -> silently use write capability
```

unless mutation was explicitly allowed.

## 4. Runtime EvidenceReceipt

The execution receipt contains:

- plan fingerprint;
- execution status;
- candidate and evidence SHAs;
- freshness boolean;
- required and unresolved outputs;
- actions still requiring an external handler;
- observations per capability;
- output fingerprints;
- sources;
- M+ / M- records;
- learned health snapshot;
- OAK status;
- a stable receipt fingerprint.

R0.2 OAK PASS requires all three:

```text
plan READY
AND runtime outputs complete
AND candidate_sha == evidence_sha
```

It does **not** certify semantic correctness, scientific truth, external authorization,
or that a pull request should be merged.

## 5. Health learning

`learn_health()` compiles outcome records into a deterministic next health snapshot.

Current conservative rules:

- successes only -> `PASS`;
- any mixed failure/degraded evidence -> `DEGRADED`;
- two failures and no successes -> `FAIL`;
- no evidence -> `UNKNOWN`.

The receipt preserves both positive memory `M+` and negative memory `M-`.

## 6. R0.1 PR #415 benchmark retained

The first live benchmark remains the PR #415 diagnosis:

```text
CI failure
 -> generic logs DEGRADED
 -> specialized GitHub Actions logs
 -> exact cause: pytest missing
 -> refresh PR state
 -> abandon stale repair after merge
```

That failure mode is encoded permanently in Capability OS CI, which installs `pytest`
explicitly before the test suite.

## Commands

Existing planning:

```bash
python -m omega_capability_os_t describe examples/capability_os_registry.json

python -m omega_capability_os_t plan \
  examples/capability_os_registry.json \
  examples/capability_os_intent_pr_ci.json \
  --health examples/capability_os_health_pr415.json
```

Compile an existing WorkUnit:

```bash
python -m omega_capability_os_t workunit-plan \
  examples/capability_os_workunit.json \
  --completed-dependency WU-PREV
```

Learn the next health snapshot from a receipt/outcome file:

```bash
python -m omega_capability_os_t learn-health receipt.json
```

## Tests

R0.2 adds integration tests for:

- WorkUnit dependency gating;
- elevated-risk mutation gating;
- successful handler execution;
- exact-SHA OAK receipts;
- unavailable-handler `ACTION_REQUIRED`;
- fallback output/authority preservation;
- stale evidence rejection;
- M+ / M- health learning.

CI runs the Capability OS suite on Python 3.10, 3.11, 3.12 and 3.13.

## Next convergence

The next high-value layer is **R0.3 external execution adapters**:

```text
Capability plan
 -> adapter contract
 -> ChatGPT/GitHub/Drive/Gmail/etc. invocation
 -> normalized tool receipt
 -> capability health update
 -> resume suspended plan
```

External adapters must remain explicit about permissions and must never convert tool
availability into permission to perform a write.
