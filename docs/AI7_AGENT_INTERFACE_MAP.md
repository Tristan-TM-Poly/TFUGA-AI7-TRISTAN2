# AI7 Agent Interface Map

Status: `formal_definition`  
OAK gate: `needs_test`  
CVCD invariant: `agent_interface_separation`

## Purpose

Define how AI7 / AIT agents should interact with the Tristan canon without mixing roles.

## Agent interfaces

| Interface | Responsibility | Output |
|---|---|---|
| Canon Reader | reads source/canon docs | summaries and invariant candidates |
| OAK Auditor | checks claim status | warnings, blockers, M_MINUS stubs |
| Prototype Builder | turns theory cards into code | small tests and examples |
| Benchmark Runner | measures claims | metrics, baselines, logs |
| PR Publisher | packages changes | branches and draft PRs |
| Residue Curator | stores failures | negative memory cards |

## Minimal contract

Each agent output should include:

- source path or provenance;
- claim status;
- OAK gate;
- CVCD invariant;
- next action;
- failure condition.

## Next actions

- Add a JSON schema for agent outputs.
- Add a dry-run example loop.
- Link validated prototypes back to `TTM-TFUGA-AI7-TRISTAN2`.
