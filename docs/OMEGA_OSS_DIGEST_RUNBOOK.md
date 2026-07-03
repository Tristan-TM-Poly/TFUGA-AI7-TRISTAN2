# Ω-OSS-DIGEST Runbook

## First run command set

```bash
oss-digest compile-github "software bill of materials" "license scanner" --language Python --license-id apache-2.0
oss-digest github-search "software bill of materials" "license scanner" --language Python --limit 5
oss-digest scan-local .
```

## OAK order of operations

1. Search only.
2. Record provenance.
3. Classify license.
4. Run local secret/dependency scan if source is cloned.
5. Generate OAK report.
6. Decide: use wrapper / rewrite invariant / block / M⁻ archive.
7. Only then integrate.

## Do not automate yet

- Do not publish secret findings.
- Do not auto-open upstream PRs without a diff and report.
- Do not copy code from StackOverflow by default.
- Do not integrate AGPL/GPL code into mixed-license/commercial targets without review.
