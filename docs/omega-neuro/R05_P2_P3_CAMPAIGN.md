# Ω-NEURO R0.5 — P2/P3 Evidence Campaign

**Status:** software-validation protocol. The current datasets are deterministic synthetic fixtures with planted effects. Passing these gates validates the harness, not the biological hypotheses.

## Purpose

R0.5 extends the evidence machinery beyond P1 so Ω-NEURO can test multiple claims under one reproducible discipline:

```text
hypothesis
-> explicit observation contract
-> simple baseline
-> richer candidate
-> group-safe held-out evaluation
-> ablations
-> negative control
-> OAK complexity/uncertainty penalty
-> evidence report
```

Mandatory invariant:

```text
synthetic recovery != biological evidence
```

## P2 — Synaptic State Tensor

### Question

Does a multidimensional synaptic state representation predict transmission-related targets better than a scalar synaptic proxy after paying for added complexity?

### Synthetic observation vector

```text
(release_probability,
 quantal_scale,
 delay_ms,
 short_term_gain,
 long_term_gain,
 context)
```

The scalar baseline sees only:

```text
w_scalar = release_probability * quantal_scale
```

The candidate sees the scalar proxy plus delay, short/long-term gain, context and a scalar×context interaction.

### Required controls

- **remove_context** — tests whether contextual terms buy predictive value;
- **collapse_plasticity** — removes short/long-term state variables;
- **permute_context** — preserves the marginal context distribution while destroying its alignment with the target.

### Software gate

The candidate must:

1. beat the scalar baseline in held-out group folds;
2. remain preferred after OAK complexity/uncertainty penalties;
3. lose measurable performance under both ablations;
4. lose measurable performance when context labels are deterministically permuted.

### Biological promotion boundary

A real P2 test would additionally require a source where the proposed state variables are independently measured or defensibly estimated, appropriate repeated-measures grouping, preregistered feature definitions, suitable alternative synapse models, uncertainty on measurements, and replication outside the fitting source.

## P3 — Higher-Order Wiring

### Question

Do higher-order circuit motifs carry predictive information beyond pairwise connectivity summaries?

### Synthetic observation vector

```text
(pairwise_strength,
 recurrence,
 motif_order3,
 motif_order4,
 context)
```

The baseline sees only pairwise strength and recurrence. The candidate additionally sees order-3/order-4 motif summaries, context and motif×context interactions.

### Required controls

- **collapse_to_pairwise** — removes all higher-order motif information;
- **remove_context** — keeps motif values but removes contextual modulation;
- **permute_higher_order_motifs** — preserves motif marginals while breaking motif/target alignment.

### Software gate

The candidate must:

1. beat the pairwise baseline under group-held-out evaluation;
2. survive OAK complexity/uncertainty penalties;
3. degrade when higher-order information is collapsed;
4. degrade strongly when motif labels are permuted.

### Biological promotion boundary

A real P3 test requires a circuit dataset with explicit provenance, a declared definition of motif order, controls for density/proximity/cell type and sampling bias, group-safe splits across cells/animals/volumes as appropriate, pairwise baselines strong enough to be credible, and replication across a second condition or dataset.

## Shared leakage barrier

P1, P2 and P3 now reuse the same generic `group_kfold()` protocol. Records need only stable `sample_id` and `group_id` fields.

This prevents a model from appearing to generalize merely because repeated measurements from the same biological or experimental unit were split across training and evaluation.

## Campaign output

Run:

```bash
python -m omega_neuro_t.campaign_cli --hypothesis all --pretty
```

The combined report contains:

- P2 evidence report;
- P3 evidence report;
- OAK decisions;
- ablation deltas;
- negative-control degradation;
- dataset manifests and split signatures;
- `software_validation_passed`;
- `biological_promotion_allowed: false`.

The last field is intentionally hard-gated to false for the synthetic campaign.

## Next empirical step

R0.6 should not add another synthetic hypothesis unless it improves the evaluator. Priority is to map one real public or consented dataset into the frozen observation contracts and run the same evaluation rules without tuning thresholds after seeing the results.
