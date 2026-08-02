# M− — Ω-ORG-FAM-T R0.2 direct-script import bootstrap

## Failure

The Ultra unit tests passed in GitHub Actions, but direct execution of `tools/generate_omega_org_fam_r02_ultra.py` failed because Python placed `tools/`, not the repository root, on `sys.path`.

## Cause

Test execution inherited the repository root through the pytest configuration. Direct script execution did not. The two execution surfaces therefore had different import semantics.

## Correction

The script now inserts its resolved repository root before importing `omega_org_fam_t`. CI continues to test both import surfaces.

## Anti-regression rule

Every executable tool must be tested in the same invocation form documented for users and used by GitHub Actions. Passing module tests alone does not certify direct-script packaging.
