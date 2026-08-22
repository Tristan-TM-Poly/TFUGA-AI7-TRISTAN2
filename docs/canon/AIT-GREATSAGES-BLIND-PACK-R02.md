# GreatSages Blind Discovery Pack — R0.2 security addendum

This addendum supersedes the earlier R0.2 roadmap note that contestant/evaluator schema separation was future work. It is now implemented in `sage_tristan/greatsages_blind.py`.

## Threat model

A rediscovery benchmark is invalid if a contestant can infer the hidden target from metadata rather than the historically gated knowledge state.

Leak channels include:

- plaintext target discovery ID;
- title;
- problem statement;
- compressed invariant;
- named descendants;
- a tournament identifier embedding the target name;
- post-gate discoveries that imply the answer.

## Physical split

`ContestantPack` contains only:

- opaque tournament ID;
- sage ID;
- gate year;
- allowed knowledge atom IDs;
- visible pre-gate discoveries;
- task contract;
- scoring axes;
- explicit withholding flags.

`EvaluatorSecret` contains:

- target discovery ID;
- target year/title;
- masked discovery set;
- descendant set;
- target digest.

The two packs share only the opaque tournament ID.

## Opaque ID

The public tournament ID is derived from a SHA-256 digest and never contains the target discovery ID in plaintext.

A digest is not a security proof against every side channel. Its purpose here is deterministic evaluator/contestant joining without carrying the target name through the contestant schema.

## Runtime leakage audit

`contestant_payload()` serializes the outgoing contestant object and explicitly checks that these target strings do not occur:

- discovery ID;
- title;
- problem statement;
- compressed invariant.

The CI additionally checks that the known modeled descendant of the Ceres seed (`gauss_1809_theoria_motus`) is absent from the visible contestant state.

## OAK boundary

Passing this gate means only:

```text
PASS = no tested target metadata leakage through the current serialized pack
```

It does not prove that an LLM cannot recover a historically later result from its pretrained internal weights. A stronger benchmark therefore also needs model-side knowledge controls, retrieval isolation, adversarial prompt audits and evaluation against memorization baselines.

This distinction is mandatory:

```text
context leakage control != model pretraining erasure
```
