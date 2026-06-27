# Ω-LEARN-T v0.2 ZERO-TOUCH workflow

```bash
python -m omega_learn_t.cli init .learning_state
python -m omega_learn_t.cli log examples/physics_learning.json --store .learning_state
python -m omega_learn_t.cli queue examples/physics_learning.json --days 7
python -m omega_learn_t.cli export-anki examples/physics_learning.json --output omega_cards.csv
python -m omega_learn_t.cli github-issue examples/physics_learning.json --type learning_goal
```

The goal is to minimize manual work while preserving explicit OAK checks before canonization.
