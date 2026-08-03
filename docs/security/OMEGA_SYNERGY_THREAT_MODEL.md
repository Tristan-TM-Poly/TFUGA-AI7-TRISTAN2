# Ω-SYNERGY-T∞ threat model

## Protected assets

- private intellectual property and unpublished theories;
- repository credentials and write authority;
- provenance and evidence integrity;
- scientific and commercial reputation;
- CI budgets and developer attention;
- user, institution and customer data.

## Principal threats

1. **Circular evidence:** two agents repeat the same source as independent confirmation.
2. **Metric gaming:** generated systems optimize the scalar score without producing useful gain.
3. **Prompt or document injection:** scanned text attempts to alter execution authority.
4. **License contamination:** incompatible code or text is treated as reusable.
5. **Interface laundering:** transformations silently discard uncertainty or provenance.
6. **Combinatorial denial of service:** candidate expansion exhausts CI resources.
7. **PR collision:** separately valid mutations conflict when composed.
8. **Stale confidence:** old validations survive dependency or data changes.
9. **IP leakage:** productization publishes material before an IP gate.
10. **Automation escalation:** a review-only artifact is interpreted as merge or deployment authorization.

## Controls present in R1

- bounded file, node, beam and order limits;
- no execution of scanned content;
- review-only authority constants;
- explicit risk and uncertainty dimensions;
- declared interface losses;
- baselines, ablations, controls and rollback;
- hash-chained evidence ledger;
- half-life revalidation;
- conflict-aware PR waves;
- CI permissions restricted to `contents: read`.

## Residual risks

- semantic extraction remains heuristic;
- text-based capability inference can be incomplete or wrong;
- no complete software bill of materials or license solver is included;
- hash chains do not establish truth;
- portfolio scoring is not calibrated to market outcomes;
- beam search can miss valuable candidates;
- repository code may encode capabilities absent from documentation.

## Promotion gates

Before enabling any write actuator, require separate review for least privilege, branch scope, dry-run, explicit approval, audit log, rollback, rate limits, secrets isolation and incident response.
