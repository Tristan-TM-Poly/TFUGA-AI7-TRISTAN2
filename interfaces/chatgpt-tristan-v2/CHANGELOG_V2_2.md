# ChatGPT Tristan OS v2.2 Changelog

## Added

- New v2.2 Iteration Cockpit tab.
- Iteration chain prompt builder for multiplier -> selector -> execution pack -> response impact.
- Heuristic session impact estimator.
- `app.v22.js` addon loaded after v2.1.
- Validator coverage for v2.2 markers.

## Connected backend tools

- `omega_iteration_execution_pack.py` builds execution prompts and impact inputs from selected batches.
- `omega-iteration-execution-pack.yml` runs the full chain in CI.

## OAK boundary

- Generate 1024 candidates, but execute only selected bounded batches.
- Heuristic impact score is not validation.
- Prototype remains separate from proof.
