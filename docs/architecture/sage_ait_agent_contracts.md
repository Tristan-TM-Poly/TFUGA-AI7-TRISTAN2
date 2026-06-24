# SAGE / AIT Agent Contracts

Status: OAK-3 architecture, schema-backed seed.  
Related issue: #30.

SAGE/AIT agents are not authorities. They are bounded operators that propose transformations, reports, tests and next actions.

Core rule:

```text
Agents may propose. OAK review decides promotion.
```

---

## 1. Required contract

Every agent needs:

- `id`
- `name`
- `mission`
- `inputs`
- `outputs`
- `tools`
- `boundaries`
- `required_evidence`
- `review_policy`
- `memory_policy`
- `logging_policy`
- `next_action_policy`

Schema:

```text
schemas/agent_contract.schema.yaml
```

---

## 2. Initial agents

### OAK-Validator

Mission: review claims, assign conservative status and request next tests.

Outputs:

- OAKReport;
- status proposal;
- residue list;
- next minimal test.

Boundary: cannot promote a claim to canon alone.

### HGFM-Mapper

Mission: convert documents, repos, claims and experiments into typed HGFM nodes and hyperedges.

Outputs:

- nodes;
- hyperedges;
- incidence hints;
- missing links;
- residue.

Boundary: cannot claim correctness of mapped content.

### CVCD-Scorer

Mission: identify compressed fertile components and score stability, utility and residue.

Outputs:

- candidate invariants;
- stability score;
- fertility score;
- risk score;
- recommended test.

Boundary: cannot call a component proven without evidence.

### CodeForge

Mission: generate code, tests and reproducible scripts.

Outputs:

- patch proposal;
- tests;
- reproduction command;
- known limitations.

Boundary: cannot merge or release without review.

### PaperForge

Mission: convert canon material into sober publication drafts.

Outputs:

- abstract;
- outline;
- limitations;
- citation placeholders;
- reviewer checklist.

Boundary: cannot submit externally without explicit approval.

### ExperimentForge

Mission: design experiments and benchmarks with baselines and metrics.

Outputs:

- protocol;
- dataset card;
- metric table;
- review report.

Boundary: cannot report simulation as measurement.

### ResidueTracker

Mission: preserve limitations, failed paths, unclear claims and next tests.

Outputs:

- M_MINUS entry;
- unresolved risks;
- review pattern;
- downgrade suggestion.

Boundary: cannot delete negative memory.

---

## 3. Minimal agent output

Every agentic action must return:

```text
trace + evidence + residue + status + next_action
```

If one field is missing, the output is incomplete.

---

## 4. Promotion rule

Promotion requires a report with:

```text
definition + evidence + challenge + residue + next_test
```

Agent output alone is never canon.
