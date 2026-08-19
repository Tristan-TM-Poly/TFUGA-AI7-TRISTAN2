# TFUGA to Prototype Bridge

Status: `prototype`  
OAK gate: `needs_test`  
CVCD invariant: `theory_to_executable_path`

## Purpose

Define the path from a TFUGA/HGFM theory fragment to a small executable prototype.

## Bridge steps

1. Select one theory card.
2. Extract one CVCD invariant.
3. Define the smallest falsifiable behavior.
4. Create a pure-Python prototype.
5. Add one positive test and one failure test.
6. Run OAK claim linting.
7. Promote only if the result clarifies or validates the theory.

## Output template

```text
theory_card -> invariant -> function -> test -> benchmark/log -> M_PLUS or M_MINUS
```

## Anti-overclaiming rule

A prototype demonstrates behavior in code. It does not prove the full theory unless a separate proof artifact exists.
