# Ω-MATH-PROOF-RESEARCH-OS — ecosystem integration

R0.1 is a vertical slice, not a replacement for the existing Tristan research stack.

## Canonical route

```text
Intent
  -> WorkUnit(kind=math_proof_research)
  -> Ω-DOC-HARVEST-T∞ / source acquisition
  -> SourceAnchor + EvidenceReceipt
  -> MathIR / MathArtifact extraction
  -> ConceptGraph + TheoremGraph + ProofGraph + ExerciseGraph
  -> ProofGenome / ConceptGenome candidates
  -> Proof/Falsification portfolio
  -> formalization candidate
  -> pinned formal kernel
  -> semantic round-trip gate
  -> OAK / M+ / M- / M?
  -> reusable research artifact
```

## Reuse-first rule

This package owns only the mathematics-specific contracts and baselines needed for the first vertical slice. Generic provenance, OAK, GitHub automation, memory, research-factory, and action/execution responsibilities should stay in their existing ecosystem components. Do not clone those systems here merely to make this package look self-contained.

## Status lattice

A mathematical object may independently have these statuses:

```text
source_discovered
source_fetched
source_hashed
source_extracted
formalization_candidate
compiled
kernel_accepted
semantic_match
OAK_verified
redistributable
```

No edge in this list is implicit. In particular:

- discovered != fetched
- fetched != true
- extracted != proved
- kernel_accepted != semantic_match
- mathematically proved != empirically validated
- accessible != redistributable

## R0.1 success criteria

1. Reconstruct and validate the 64-source discovery contract without committing third-party PDF bytes.
2. Keep a five-source proof-kernel pilot runnable independently.
3. Emit provenance-preserving `MathArtifact` objects.
4. Demonstrate deterministic extraction and Proof ISA baselines.
5. Produce formalization candidates while refusing to label them proved before kernel CI.
6. Establish benchmark hooks for later comparison against plain retrieval / plain LLM baselines.

## R0.2 target

R0.2 should add the first end-to-end measured path:

```text
source page
 -> extracted theorem/proof
 -> MathArtifact
 -> ProofGenome
 -> retrieved analogue
 -> generated formalization
 -> kernel result
 -> semantic round-trip score
 -> EvidenceReceipt
```

The next release is justified only if it yields measurable gain over simpler baselines.
