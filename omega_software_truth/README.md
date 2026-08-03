# Ω-CS-SOFTWARE-TRUTH

Treat every callable as a behavioral hypothesis.

## Core object

```text
SoftwareState = (I, O, A, E, T, R, M)
```

Where:

- `I`: input contract
- `O`: output contract
- `A`: callable/algorithm
- `E`: environment note
- `T`: executable examples
- `R`: residues emitted by validation
- `M`: positive/negative memory

## Minimal use

```python
from omega_software_truth import Contract, ExampleCase, OAKValidator, SoftwareState


def add(a, b):
    return a + b

contract = Contract(
    name="addition",
    input_predicates={"two_ints": lambda args, kwargs: len(args) == 2 and all(isinstance(x, int) for x in args)},
    output_predicates={"int_output": lambda output: isinstance(output, int)},
)

state = SoftwareState(
    name="add",
    target=add,
    contract=contract,
    examples=(ExampleCase("simple", args=(2, 3), expected=5),),
)

report = OAKValidator().validate(state)
print(report.to_markdown())
```

## OAK status

Current status: **C — executable prototype**.

It may become **D — demonstrated locally** when tests pass in CI or a reproducible local run is recorded.
