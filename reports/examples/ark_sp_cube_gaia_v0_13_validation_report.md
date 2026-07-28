# ARK-SP-CUBE-GAIA v0.13 Validation Report

Status: `C_plus_validation_scaffold`

This report documents the intended validation scope for v0.13. It is not a test result from GitHub Actions and it is not a physical, legal, financial, patent, or carbon-credit validation.

## Validation scope

The v0.13 validation layer checks only:

1. required JSON artifacts exist;
2. JSON files parse correctly;
3. OAK-Lint rules include blocked patterns and safe rewrites;
4. global OAK boundary fields keep certification, revenue, public-sector decision, and patent claims set to `false`;
5. selected forbidden phrases are not present in machine-readable JSON artifacts.

## Expected command

```bash
python scripts/validate_ark_sp_cube_gaia_v0_13.py
```

Expected output when local files are present and shaped correctly:

```text
ARK-SP-CUBE-GAIA v0.13 validation: PASS
Scope: JSON shape and OAK wording guardrails only.
Non-claims: no physical validation, no revenue, no certification.
```

## Explicit non-claims

This validation report does not claim:

- SP-CUBE cooling performance is measured;
- Ark-M1 is a certified energy product;
- GAIA-SAT values are revenue;
- methane entries are verified carbon credits;
- patent validity or freedom to operate;
- public-sector decision authority;
- external scientific review.

## OAK freeze recommendation

After v0.13, freeze the PR scope unless a change is directly related to review, validation, citations, or safety wording.

Recommended next move:

```text
freeze -> review -> small fixes -> merge decision
```

Do not add new modules to this PR after v0.13 unless the reviewer explicitly requests them.
