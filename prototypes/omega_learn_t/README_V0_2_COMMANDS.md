# Ω-LEARN-T v0.2 commands

```bash
python -m omega_learn_t.cli diagnose examples/physics_learning.json
python -m omega_learn_t.cli coach examples/physics_learning.json
python -m omega_learn_t.cli init .learning_state
python -m omega_learn_t.cli log examples/physics_learning.json --store .learning_state
python -m omega_learn_t.cli status --store .learning_state
python -m omega_learn_t.cli queue examples/physics_learning.json --days 7
python -m omega_learn_t.cli export-anki examples/physics_learning.json --output /tmp/omega_cards.csv
python -m omega_learn_t.cli export-json examples/physics_learning.json --output /tmp/omega_report.json
python -m omega_learn_t.cli github-issue examples/physics_learning.json --type learning_goal
```

## OAK-safe note

The learning scores are diagnostic helpers. They are not definitive measurements of human cognition. Every score must remain grounded in evidence, delayed retests, transfer tasks and captured residues.
