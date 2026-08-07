# Generated Ω-GITHUB-MYCELIUM-T∞ artifacts

This directory is reserved for deterministic, reviewable campaign bundles.

Generated artifacts are evidence about software planning and supplied snapshots. They are not evidence that remote branches, commits, PRs, merges, publications or deployments occurred.

Use:

```bash
python -m omega_github_mycelium_t plan \
  --objective "Detect code-documentation divergence" \
  --root-creation omega-doc-t \
  --snapshot data/omega_github_mycelium_t/repository_snapshot_2026_08_03.json \
  --output-dir generated/omega_github_mycelium_t/demo
```

The sample snapshot contains all six owned repositories observed on 2026-08-03 but only representative pull requests. Use `live-scan` for a fresh complete open-PR snapshot.
