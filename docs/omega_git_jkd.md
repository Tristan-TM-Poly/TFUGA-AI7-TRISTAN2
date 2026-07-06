# Ω-GIT-JKD-MINUS-T

Status: C.

Purpose: keep Git changes small, clear and testable.

## Rules

- one file, one role
- prefer small modules
- add a test or demo near new code
- keep status labels honest
- record friction as M-minus

## Current helpers

- `omega_git_jkd.events`: stores useful workflow lessons
- `omega_git_jkd.sizing`: suggests `small` or `split` from line count

## Commands

```bash
python examples/omega_git_jkd_demo.py
python -m pytest tests/test_omega_git_jkd.py
```

## M-minus

Large, dense changes are fragile. Small changes are easier to review, test and land.
