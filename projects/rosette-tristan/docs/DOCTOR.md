# Rosette Doctor

`rosette-doctor` audits the local Rosette installation and produces an OAK-safe environment report.

## Command

```bash
rosette-doctor --out out_doctor/doctor_report.json
```

Strict mode for CI:

```bash
rosette-doctor --out out_doctor/doctor_report.json --require-all-commands
```

## Checks

- Python version
- platform
- installed Rosette commands on PATH
- optional modules such as `matplotlib` and `fitz` / PyMuPDF

## Output

```text
out_doctor/
  doctor_report.json
```

## OAK statuses

- `doctor_passed_not_certified`
- `doctor_review_needed_optional_render_missing`
- `doctor_failed_missing_commands`

## OAK lock

Doctor passing means the local command surface and optional environment are coherent. It does not prove extraction fidelity, PDF correctness, mathematical equivalence or scientific truth.
