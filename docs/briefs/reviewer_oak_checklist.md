# Reviewer OAK Checklist

Use this checklist before promoting any THT/HGFM object from idea to canon.

## 1. Status separation

- [ ] The object has a clear status: narrative, concept, formalized, simulation-ready, simulated, measurement-ready, measured, replicated, certified, or M_MINUS.
- [ ] Simulation is not described as measurement.
- [ ] A fertile idea is not described as proven.
- [ ] A benchmark result includes baseline and metric definitions.

## 2. Definition quality

- [ ] Terms are defined before they are used.
- [ ] Inputs and outputs are specified.
- [ ] The object can be represented as a node, edge, module or report.
- [ ] Dependencies are listed.

## 3. Evidence

- [ ] There is a linked file, test, dataset, proof sketch or reproducible command.
- [ ] Evidence is enough for the claimed status.
- [ ] Missing evidence is listed as residue.

## 4. Challenge and limitations

- [ ] At least one limitation is stated.
- [ ] At least one failure condition is stated.
- [ ] There is a next minimal test.
- [ ] Risky patterns are routed to M_MINUS.

## 5. Reproducibility

- [ ] Commands are provided when applicable.
- [ ] Randomness is seeded when applicable.
- [ ] External tools are optional or documented.
- [ ] The expected output is described.

## 6. Promotion rule

Promote only if:

```text
definition + evidence + challenge + residue + next_test
```

Otherwise keep active, downgrade, or route to M_MINUS.
