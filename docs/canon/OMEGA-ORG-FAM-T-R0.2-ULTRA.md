# Ω-ORG-FAM-T R0.2 Ultra

## 68.7 billion addressable objects, 67.1 million materialized objects

**Status:** executable OAK-safe research infrastructure. It is not a database of certified molecules and it does not certify synthesis, stability, spectra, toxicity, biological action, novelty or patentability.

## Scale

The R0.2 registry has twelve typed axes: skeleton, functional family, electronic class, reaction archetype, stereochemical class, physical environment, isotope profile, protonation or charge state, conformer class, solvent class, temperature regime and pressure regime.

```text
17,179,869,184 family addresses
68,719,476,736 linked family + evidence addresses
```

The first Ultra frontier materializes:

```text
16,777,216 family records
50,331,648 evidence/control records
67,108,864 total objects
```

This is a finite experiment, not a permanent maximum. Every run remains bounded by compute, storage, CI, quality, provenance, safety and rollback budgets.

## Fixed-width packing

R0.2 stores one four-byte record per materialized family and one byte per evidence template. Identifiers and links are reconstructed exactly from position and the versioned registry. This avoids counting repeated JSON keys and duplicated strings as knowledge.

Family record `<BHB>` stores compatibility percentage, contradiction bitset and warning flags. Evidence bytes store evidence kind and modality. Every shard has SHA-256; shard hashes form a Merkle root; the registry has a canonical fingerprint.

## New executable layers

- external registry loader and exact mixed-radix codec;
- compact OAK contradiction bitsets;
- adaptive frontier controller with checkpoint, M+ and M−;
- Raman/FTIR family grammar with counter-signatures;
- reaction grammar requiring atom and charge balance;
- deterministic fixed-width sharding and Merkle audit;
- CLI for statistics, encode, decode, generation, audit and spectral evaluation.

## OAK distinctions

```text
address != molecule
family compatibility != molecular identity
spectral marker != unique assignment
reaction template != validated mechanism
balanced equation != practical synthesis
generated evidence template != experimental evidence
large atlas != discovery count
compression != proof
```

## Commands

```bash
omega-organic-family-ultra stats
omega-organic-family-ultra decode 4294967296
omega-organic-family-ultra generate generated/omega_org_fam_t_r02_ultra --family-records 16777216
omega-organic-family-ultra audit generated/omega_org_fam_t_r02_ultra
python tools/generate_omega_org_fam_r02_ultra.py --root . --clean
```

## Next scientific frontiers

Reviewed SMARTS/SMIRKS registries; optional RDKit/Open Babel validation; atom-mapped reaction hyperedges; Raman/FTIR/NMR/MS ranges with source-level provenance; mixture inference and symbolic physical deconvolution; held-out calibration; tautomer, resonance, salt, solvate and polymorph layers; property/hazard applicability domains; distributed checkpointed generation; independent OAK promotion.

The purpose of scale is to make the search space addressable, testable and falsifiable. Volume never upgrades epistemic status by itself.
