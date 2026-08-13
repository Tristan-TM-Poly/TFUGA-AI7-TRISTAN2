# Ω-GITHUB-CUMULATIVE-INTELLIGENCE-T∞ — R0.8→R1.2

This extension turns the existing cumulative PR memory into a read-only, reuse-first historical intelligence layer for future Global/PR/Module/Theory/System/Application/Creation LLMT views.

It is stacked on:

```text
#417 Ω-CAPABILITY-OS-T∞
→ #447 Ω-GITHUB-CUMULATIVE-MEMORY-T∞ R0.1→R0.7
→ #448 Ω-UNIVERSAL-RESEARCH-ABI-T∞ R0.1→R0.2
→ this PR
```

The implementation deliberately reuses:

- `GitHubMemoryIndex`
- `PRMemory`
- `ReuseBeforeCreateGate`
- Progressive Zoom / static AST assets
- `ResidualCodeCompiler`
- `LLMTFederationCompiler`
- the #448 Research ABI bridge boundary

No competing capability ontology or second PR memory substrate is introduced.

## Operating law

```text
SEARCH ALL HISTORY BEFORE CREATE
→ REUSE BEFORE CREATE
→ COMPOSE BEFORE DUPLICATE
→ EXTEND BEFORE FORK
→ INSPECT BEFORE ASSUME
→ CONSULT M-
→ CREATE ONLY THE RESIDUAL
→ TEST
→ RECORD OUTCOME
→ FEED RESULT BACK TO MEMORY
```

## R0.8 — Complete lifecycle archaeology

The #447 live snapshot already queries GitHub with `state=all`. R0.8 makes the resulting lifecycle partition explicit:

```text
OPEN
DRAFT
MERGED
CLOSED_NOT_MERGED
```

Hard boundary:

```text
MERGED != M+
CLOSED != M-
NOT_MERGED != useless
```

Closed and unmerged PRs remain searchable historical experiments. M+/M-/M? still require explicit evidence-bearing outcome receipts.

## R0.9 — PR Genome

Each indexed PR can be compressed into a `PRGenome` containing:

```text
identity + lifecycle + head SHA
named Ω concepts
intent tokens
changed files
asset IDs
static AST symbol assets already discovered by #447 Zoom
failure-memory lines
lineage neighborhood
```

The genome is a retrieval artifact, not a semantic-equivalence certificate.

## R1.0 — Multi-axis lineage archaeology

The compiler preserves existing explicit #447 graph edges and adds additive historical signals for directives such as:

```text
reconstructs:
stacked on:
converges:
source pr:
```

Cross-repository `owner/repo#N` references remain repository-qualified.

These lineage signals help distinguish:

```text
commit ancestry
content ancestry
capability ancestry
theory/system ancestry
historical reconstruction/convergence
```

without claiming causal dependence from text similarity.

## R1.1 — Minimal Reuse Coalition

For explicit Capability contracts, the compiler greedily selects a small coalition whose declared outputs cover the requested outputs.

```text
required outputs
→ existing capability contracts
→ minimal useful coalition
→ covered outputs
→ residual outputs
```

Historical PR similarity remains only an exact-inspection queue.

`reuse_coverage_ratio` therefore measures explicit contract-output coverage, not implementation compatibility or correctness.

## R1.2 — One Memory, Many LLMT Lenses

The same canonical memory can emit bounded views for:

```text
global
repository
PR
module
theory
system
application
creation
```

The implementation does not create independent private memories or independent evidence streams. LLMT lenses are bounded selectors over one external memory substrate.

A compiled context capsule contains:

- exact history coverage receipt;
- minimal reuse coalition;
- relevant PR genomes;
- lineage neighborhood;
- M- / failure-memory hits;
- repository-specific residual courts;
- existing #447 LLMT federation packets;
- specialized memory lenses;
- immutable generation constitution;
- OAK boundaries and deterministic fingerprint.

## Cross-repository mode

The CLI accepts repeated canonical #447 indexes:

```bash
python -m omega_capability_os_t.github_cumulative_intelligence_cli \
  examples/github_cumulative_intelligence_request.json \
  --index owner/repo-a=/tmp/repo-a.json \
  --index owner/repo-b=/tmp/repo-b.json \
  --index owner/repo-c=/tmp/repo-c.json \
  --output /tmp/cumulative-intelligence.json
```

Each source index should be refreshed through the existing read-only #447 snapshotter. Repository-scoped GitHub Actions tokens must not be silently widened to cross-repository write/read authority.

## Exact-head court

```bash
python -m compileall -q omega_capability_os_t omega_research_abi_t
pytest -q tests/test_omega_github_cumulative_intelligence.py
```

The workflow additionally performs a live `state=all` snapshot of the current repository, compiles the new intelligence capsule, and retains bounded artifacts.

## OAK non-claims

This PR does not claim:

- merged PR = successful experiment;
- closed PR = failed experiment;
- textual similarity = semantic equivalence;
- AST symbol existence = reusable behavior;
- lineage mention = causal proof;
- contract-output coverage = implementation compatibility;
- many LLMT views = independent evidence;
- historical utility = present validity;
- generation permission = GitHub write authority;
- complete cross-repository truth from a repository-scoped workflow.

The intended effect is narrower and measurable:

```text
less reinvention
+ more historical reuse
+ stronger provenance
+ explicit negative memory
+ smaller residual PRs
+ bounded LLMT context
```
