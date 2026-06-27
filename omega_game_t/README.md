# Omega GAME T — Core Split

Issue: #90  
Status: small merge unit split from the larger GAME branch.

## Scope

This PR adds only the first reviewable unit:

- graph primitives;
- event validation;
- quality scoring;
- OAK gate;
- tests.

## Boundary

Omega GAME T is a game, simulation, and research lab. It is not a tool for manipulation, unfair automation, or unsafe real-world instructions.

## Local test

```bash
cd omega_game_t
python -m pytest
```

## Next split units

1. memory plus GM agent;
2. TextWorld engine;
3. Quest-CVCD;
4. tests and docs;
5. GameQualityScore benchmark.
