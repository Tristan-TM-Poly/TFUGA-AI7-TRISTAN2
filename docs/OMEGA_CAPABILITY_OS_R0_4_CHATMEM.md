# Ω-CAPABILITY-OS-T∞ R0.4 — External Side-Effect Contracts + ChatMem Bridge

Status: **executable prototype / bounded external handoff / ChatMem continuity compiler / human-authorized writes only**

## Why R0.4 exists

R0.3 established a deterministic suspend/resume boundary:

```text
Capability plan
→ ExternalActionRequest
→ real connector invocation outside the package
→ ExternalActionReceipt
→ resume
```

That closed the gap between a Python planner and real ChatGPT connectors, but it left
one important safety question too implicit:

> Does the external action have the same side-effect level as the Capability node that
> selected it?

An arbitrary binding name is not a security boundary. A capability labelled `read`
must not be able to point at a mutating provider action and inherit the read permission.

R0.4 makes that mismatch executable and fail-closed.

It also uses that stricter external contract to connect Ω-CAPABILITY-OS-T∞ with
Ω-CHATMEM-HGFM-T∞.

---

## 1. Two authority layers

R0.4 distinguishes:

1. **Capability authority** — the maximum effect the planning node is allowed to request.
2. **External authority** — the real side-effect class of the connector action.

The ordering is:

```text
read < draft < write < irreversible
```

and every binding must satisfy:

```text
external_authority <= capability.authority
```

Examples:

```text
Capability(read)  → GitHub.fetch_file(read)                 PASS
Capability(write) → GitHub.fetch_file(read)                 PASS
Capability(read)  → GitHub.update_file(write)               FAIL
Capability(write) → GitHub.merge_pull_request(irreversible) FAIL
```

A provider word such as “draft” does not determine authority. If an operation persists
state remotely, the binding must be labelled `write` unless the operation is truly
irreversible.

Legacy R0.3 bindings that omit `external_authority` default to `read`, preserving the
existing read-only examples.

---

## 2. Mutation attestation in receipts

`ExternalActionReceipt` now contains:

```text
mutation_performed: bool
mutation_refs: [ ... ]
```

Receipt validation applies two additional laws.

### Non-mutating request

```text
external_authority in {read, draft}
AND mutation_performed == true
→ FAIL
```

### Mutating request

```text
external_authority in {write, irreversible}
AND status == SUCCESS
AND mutation_performed == false
→ FAIL
```

This does not make a self-reported receipt a cryptographic proof of provider behavior.
It prevents the execution layer from silently translating “success” into a mutation
claim without stating what happened.

Where possible, `mutation_refs` should point to concrete provider identities such as a
commit SHA, message/draft ID, event ID, Library path/version or other returned object.

---

## 3. ChatMem R0.4 capability family

`omega_capability_os_t.chatmem` compiles the existing cross-conversation memory protocol
into typed Capability OS nodes.

It does **not** replace the ChatMem compiler, HGFM representation, privacy rules or
checkpoint format. It only owns capability selection, ordering, authorization and
external receipts.

### 3.1 Bootstrap

The bootstrap intent requires:

```text
chatmem_pointer_candidates
chatmem_context_candidates
```

Preferred path:

```text
Files/Library semantic pointer search
→ Files/Library relevant-context search
```

Fallbacks:

```text
GitHub fetch pointer
GitHub fetch known context capsule
```

Every bootstrap capability is `read`.

Default source identities match the live protocol:

```text
repository:
  Tristan-TM-Poly/TFUGA-AI7-TRISTAN2

pointer:
  memory/chatgpt/CHATMEM_GLOBAL_POINTER.json

library:
  /Tristan/ChatGPT Memory
```

The helper `default_chatmem_bootstrap_values(topic)` constructs the smallest initial
retrieval state for a topic.

### 3.2 Checkpoint preflight

Before any persistence capability can be selected, the local
`chatmem.validate_checkpoint` node must produce `checkpoint_gate`.

The manifest must satisfy:

```text
checkpoint_id != empty
previous_checkpoint != empty
oak_status == PASS
public_derivation_only == true
raw_transcript_committed == false
source_hashes != empty
```

Invalid manifests fail before an external write request is emitted.

### 3.3 Persistence sequence

The write-enabled checkpoint plan is:

```text
checkpoint_manifest
→ local checkpoint_gate

checkpoint_gate
→ files.manage_library upload
→ library_persistence_receipt

checkpoint_gate
→ GitHub.create_file public-derived checkpoint
→ github_checkpoint_receipt

checkpoint_gate
+ library_persistence_receipt
+ github_checkpoint_receipt
→ GitHub.update_file global pointer
→ github_pointer_update_receipt
```

The global pointer update therefore depends on **both** durable persistence surfaces.

This prevents the failure mode:

```text
one surface succeeds
→ pointer advances
→ other surface missing
→ canonical memory falsely claims full checkpoint persistence
```

---

## 4. Permission boundary

`chatmem_checkpoint_intent()` defaults to:

```text
allow_mutation = false
```

so the persistence graph is `HOLD`.

Only an explicitly write-authorized intent can select the Library/GitHub mutation
capabilities.

No R0.4 code authorizes merge, auto-merge, public release, external messaging,
deletion, permission widening, secret access, IP disclosure or irreversible action.

---

## 5. Suspend/resume semantics

The external runtime remains single-frontier and deterministic.

Example checkpoint progression:

```text
run 1
  local OAK gate PASS
  Library request missing receipt
  → HOLD

run 2
  Library receipt supplied
  GitHub checkpoint request missing receipt
  → HOLD

run 3
  Library + GitHub checkpoint receipts supplied
  pointer update request missing receipt
  → HOLD

run 4
  all three receipts supplied
  exact candidate/evidence SHA match
  → COMPLETE / OAK PASS
```

Every rerun reconstructs the same plan fingerprint and deterministic request IDs from
the same inputs.

---

## 6. OAK boundaries

R0.4 establishes bounded software contracts only.

```text
binding authority check
!= proof that a provider action was correctly classified

mutation_performed=true
!= independent proof that the provider mutated exactly as intended

Library upload receipt
!= semantic correctness of memory contents

GitHub checkpoint commit
!= privacy correctness unless the local gate and review inputs were correct

pointer update
!= proof that inaccessible conversations were captured

OAK PASS
!= scientific truth
```

Ω-CHATMEM-HGFM-T∞ remains explicitly limited to accessible/authorized conversation
sources and PUBLIC-derived GitHub memory.

---

## 7. R0.4 executable courts

The added tests cover:

- binding manifest authority validation;
- read-only ChatMem bootstrap;
- redacted external bootstrap request;
- default checkpoint HOLD without mutation permission;
- OAK/privacy preflight blocking before any remote request;
- ordered three-stage checkpoint suspend/resume;
- pointer dependency on Library + GitHub checkpoint receipts;
- read capability → mutating binding rejection;
- fail-closed request construction even if manifest validation is skipped;
- non-mutating receipt claiming mutation rejection;
- successful write receipt without mutation attestation rejection.

Exact-head GitHub Actions remains the integration authority.

---

## 8. Next bounded frontier

R0.5 should add **provider response normalizers** rather than more abstract planner
layers:

```text
raw GitHub connector response
→ typed GitHub receipt normalizer

raw Files/Library response
→ typed Files receipt normalizer

raw Drive/Gmail/Calendar response
→ typed provider normalizer

normalized provider receipt
→ ExternalActionReceipt
```

The next quality metric should be how reliably those normalizers reject incomplete,
misbound or stale provider results — not how many connector names can be listed.
