# Ω-LEARN-T v0.2 usage examples

## Diagnose

```bash
python -m omega_learn_t.cli diagnose examples/physics_learning.json
```

## Persist

```bash
python -m omega_learn_t.cli init .learning_state
python -m omega_learn_t.cli log examples/physics_learning.json --store .learning_state
python -m omega_learn_t.cli status --store .learning_state
```

## Schedule

```bash
python -m omega_learn_t.cli queue examples/physics_learning.json --days 7
```

## Export

```bash
python -m omega_learn_t.cli export-anki examples/physics_learning.json --output omega_cards.csv
```
