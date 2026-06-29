# Demo Packet — Datacenter Energy OAK

## Purpose

This packet makes Ω-ROI-OAK and Ω-DE-TensorProd∞ concrete for universities and research/innovation offices.

It proposes a lightweight, OAK-safe microbenchmark around datacenter thermal/energy optimization. The goal is not to claim industrial validation, but to provide a clear proof-of-work artifact that can be reviewed, challenged, improved, or adapted by a university partner.

## Core demonstration

The existing repository already contains a datacenter thermal MVP:

- `omega_vtp_t/datacenter_thermal.py`
- `examples/datacenter_oak_demo.py`

The model is intentionally lightweight and auditable. It does **not** replace CFD, building physics, facility instrumentation, ASHRAE compliance review, or an industrial commissioning process.

## Microbenchmark promise

```text
Input: simulated or partner-provided lightweight thermal/energy case
Process: baseline → proposed control/surrogate → residuals → invariants → ROI-OAK
Output: OAK report with limits, risks, baseline, pilot/no-go decision
```

## Why this packet matters

Datacenter energy is a strong first proof because it is:

- concrete enough for engineering teams;
- relevant to energy efficiency and infrastructure;
- compatible with optimization, control, digital twins, and scientific AI;
- directly linked to economic metrics through cautious ROI-OAK;
- safe to start with simulated or anonymized non-sensitive data.

## Files in this packet

| File | Role |
|---|---|
| `microbenchmark_one_pager.md` | concise institutional explanation |
| `oak_report_example.md` | example OAK report using the existing demo shape |
| `university_fit_matrix.yaml` | which universities this packet fits best |
| `send_when_requested_email_fr.md` | short email to send only when a contact asks for more information |

## OAK rule

```text
This packet is a demo and pilot proposal, not a claim of industrial savings, endorsement, or validated deployment.
```
