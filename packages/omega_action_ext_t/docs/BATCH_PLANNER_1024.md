# Batch Planner 1024

Goal: apply Zero-Manual PR Forge across many Tristan repositories in one bounded planning pass.

The system should inspect up to 1024 PR-like work items per batch and classify each as:

- draft sweep;
- safe repair;
- preservation and synthesis;
- wait for checks;
- green-only shipment;
- OAK lock.

It must never weaken gates or bypass safety. The batch output is a machine queue with repository, PR number, title, action, priority, reason, draft state, mergeability, check state, OAK gate required, and green-only required.

## Repositories currently discovered

- Tristan-TM-Poly/PEFA-FractalEnergySystem
- Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG
- Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG
- Tristan-TM-Poly/TFACC
- Tristan-TM-Poly/TFUGA-AI7-TRISTAN2
- Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2

## Current global behavior

The active All-GitHub PR Forge automation should scan all accessible repositories hourly, prioritize Tristan-owned repositories, repair safe blockers autonomously, and only ship green non-draft work with expected head SHA.

## OAK invariant

One iteration may plan massively; actual external mutation remains gated, auditable, additive, and green-only.
