# Ω Meta Representation Tournament R0.2

This bounded engineering court implements issue #541. It tests whether the generic `MorphGenome` adapter earns its abstraction cost on frozen repository-derived tasks.

## Competitors

1. `morph_genome`
2. `domain_specific`
3. `minimal_dict`
4. `no_abstraction`

## Frozen domains

- meta skill planning: `omega_tristan_meta/skill_civilization.py::SkillGenome`
- value/economic: `omega_value_os/models.py::ValueGenome`
- learning scheduling: `prototypes/omega_learn_t/omega_learn_t/scheduler.py::ScheduledTask`

All fixtures are `SIMULATED_ENGINEERING`. They reuse bounded repository structures but are not empirical real-world evidence.

## Hard probes

Every competitor is checked independently for:

- required-field completion;
- evidence preservation when evidence is present;
- provenance preservation;
- exact round-trip regeneration closure;
- detection of a deleted required field.

Only hard-gate-passing candidates enter the Pareto court. The court keeps complexity bytes, deterministic execution-cost units, translation failure rate, and a frozen future-work-elimination proxy separate. `scalar_score = NOT_USED`.

## Adversarial anti-abstraction case

The learning task is deliberately marked `one_off`. No generic maintenance-reuse credit is granted. If a simpler direct representation preserves all probes at lower cost/complexity, MorphGenome must lose.

Local R0.2 court before publication observed:

```text
meta-skill-plan          -> MorphGenome remains Pareto-eligible
value-genome             -> MorphGenome remains Pareto-eligible
learning-scheduled-task  -> no_abstraction only; MorphGenome loses
status                   -> PASS
new tests                -> 11/11 PASS
```

This is a bounded falsification result, not proof that MorphGenome is generally optimal or generally inferior.

## M+/M-/M?

`M+` candidate: MorphGenome may remain Pareto-eligible when explicit cross-domain maintenance reuse offsets abstraction debt.

`M-` candidate: do not prefer MorphGenome for one-off tasks when a direct representation preserves all frozen probes at lower complexity/cost.

`M?`: the maintenance-reuse proxy still requires future validation against observed maintenance work.

## Run

```bash
python -m unittest tests.test_meta_representation_tournament -v
python -m omega_tristan_meta.representation_tournament \
  benchmarks/meta_representation_r02.json \
  --out /tmp/meta-representation-r02.json
```

## OAK boundaries

```text
Generated != Verified
GenericRepresentation != BetterRepresentation
Generator != Judge
Capability != Authority
Simulation != Reality
LocalPASS != GlobalPASS
ParetoEligible != UniversallyPreferred
SyntheticMaintenanceProxy != ObservedFutureWork
```

A PASS establishes only deterministic bounded engineering behavior on the frozen corpus. It does not authorize automatic deletion of MorphGenome, universal cross-domain claims, or external action.
