# GitHub Reactor Tools

This directory contains the local-only GitHub Autonomous Reactor kernel for the TFUGA / AI-7 / SAGE / AIT ecosystem.

## Purpose

The reactor converts a repository into an OAK-readable software node:

```text
inventory -> compile audit -> claim hygiene scan -> OAK score -> Bayes-Tristan next actions -> reports
```

## Primary script

```bash
python tools/github_reactor/repo_reactor_audit.py --repo-root . --out reports/github-autonomous-reactor
```

Outputs:

```text
reports/github-autonomous-reactor/reactor_oak_matrix.json
reports/github-autonomous-reactor/REACTOR_OAK_MATRIX.md
```

## What it does

- Counts files, suffixes, top directories and canonical paths.
- Detects package manifests.
- Parses Python files with `ast.parse`.
- Scans text files for high-risk unsupported claims.
- Computes a local OAK software scaffold score.
- Emits Bayes-Tristan next actions.
- Lists the six current repository targets in the Tristan GitHub HGFM reactor.

## What it does not do

- It does not call the GitHub API.
- It does not push commits.
- It does not merge PRs.
- It does not deploy external infrastructure.
- It does not certify physical, financial, legal, or official claims.

## OAK rule

A high score means only:

```text
repository structure is healthier and more automatable
```

It does **not** mean:

```text
mathematical proof, physical validation, official publication, deployment, or revenue validation
```

## Canonical propagation pattern

```text
root reactor scan
  -> local reports
  -> artifact upload
  -> branch packet
  -> draft PR
  -> human/OAK review
  -> canon promotion only after gates
```
