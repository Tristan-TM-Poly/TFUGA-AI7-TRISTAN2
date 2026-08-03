# R0.4 threat model and M⁻ registry

## Protected claims

R0.4 attempts to protect these transitions:

```text
certificate bytes -> verified proof graph
candidate interval -> reproducible residue receipt
artifact payload -> append-only evidence entry
checkpoint -> authenticated prefix commitment
external tool run -> bounded verifier receipt
work observation -> budget admission or rejection
```

## Threats covered

- altered certificate or graph hash;
- missing, substituted or cyclic child proof;
- unreachable proof nodes hidden in a bundle;
- altered residue rule or compiler policy;
- transparency-log payload or previous-hash mutation;
- checkpoint root, prefix or public-key substitution;
- shell injection through external verifier execution;
- artifact/verifier mismatch;
- duplicate compute observation;
- reserve exhaustion and uncontrolled task admission.

## Threats not solved

- malicious but internally consistent external verifier;
- compromised operating system or OpenSSL binary;
- stolen signing key;
- side-channel leakage;
- Byzantine distributed consensus;
- completeness of Internet-wide precedence searches;
- incorrect energy or cost telemetry;
- legal ownership, patentability or market demand;
- proof methods not represented by the current adapters.

## Fail-closed behavior

Malformed or tampered proof graphs, residue programs, checkpoints and receipts are rejected. A missing external verifier leaves the artifact at `IMPORTED_UNVERIFIED_EXTERNAL_ARTIFACT_R0_4`. Exhausted compute reserve blocks new observations instead of silently exceeding policy.
