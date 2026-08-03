# Synthetic data contract

All demand, generation, reserve, storage, corridor, capacity, reactance, exposure and repair values in `omega_hqt_t.synthetic_quebec` are deterministic research fixtures.

The 17 names correspond to administrative regions for interpretability. Connectivity is intentionally fictitious and must never be presented as Hydro-Québec topology.

Required labels for every derived artifact:

- `synthetic_fixture: true`;
- `operational_claim: false`;
- generator version and evidence hash;
- uncertainty equal to 1.0 where no external calibration exists.

No reverse-engineering of precise critical-infrastructure topology belongs in this repository.
