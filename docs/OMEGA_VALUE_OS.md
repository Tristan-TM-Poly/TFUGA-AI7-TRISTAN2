# Ω Value OS — Regenerative Monetization Kernel

## Status

Executable research/engineering kernel. It does **not** claim autonomous business
success, causal proof from observational metrics, legal compliance by default,
or authority to spend/contract/publish.

## Minimum sufficient kernel

`K_V* = {OBSERVE, RESIDUALIZE, GENERATE, TEST, DELIVER, VERIFY, ALLOCATE, LEARN, REGENERATE}`

The current implementation materializes a bounded vertical slice:

- typed Value/Strategy/Revenue genomes;
- AuthorityEnvelope and non-compensatory OAK gates;
- automation score + A0-A5 promotion;
- ProofOfBetterReceipt and meta-stop rule;
- generator mutation that cannot self-approve;
- R0-R5 regeneration vocabulary;
- verified/idempotent paid-account entitlement ledger;
- provenance-aware media projections and channel routing;
- active/passive/mixed revenue portfolio metrics;
- platform concentration and review-only prune candidates;
- bounded economic shock scenarios;
- JSON interchange schemas;
- repository-native skill + activation/adversarial evals.

## Architecture

```text
Reality / market evidence
        |
        v
 MarketResidualField
        |
        v
 ValueGenome --> Strategy population --> NO_ACTION baseline
        |                |
        |                v
        |          Shadow / adversarial tests
        |                |
        v                v
 AuthorityEnvelope --> OAK hard gates
                         |
               +---------+---------+
               |                   |
             FAIL                 PASS
               |                   |
          HOLD / PRUNE      smallest experiment
                                   |
                                   v
                          ProofOfBetterReceipt
                                   |
                        +----------+----------+
                        |                     |
                      HOLD                 PROMOTE
                                              |
                           +------------------+------------------+
                           |                  |                  |
                     Entitlements        MediaGraph       RevenuePortfolio
                           |                  |                  |
                           +------------------+------------------+
                                              |
                                   Evidence / M+ / M-
                                              |
                                         REGENERATE
```

## Objective discipline

Never optimize raw revenue alone. Use Pareto comparison across at least:

- verified user value/outcome;
- contribution margin rather than gross revenue;
- trust and retention;
- resilience and platform concentration;
- reusability and future option value;
- attention and maintenance cost;
- rights/compliance/risk.

A composite score is allowed only as a heuristic after hard constraints pass.

## Autonomous vs approval-required work

Good candidates for bounded/zero-touch automation **after evidence and explicit
scope** include analytics refreshes, report generation, content transformation,
non-sensitive scheduling, experiment analysis and reversible routing.

Keep explicit human authority for financial transfers/purchases, contracts,
tax/legal decisions, major pricing changes, sensitive public claims,
credential/permission changes and any action whose authority is unclear.

## Paid accounts and entitlements

`EntitlementLedger` deliberately separates payment-provider authority from
application access state:

- an unverified normalized event cannot change access;
- event IDs are idempotent;
- grants/revocations retain an audit lineage;
- the ledger never creates charges, refunds, payouts or subscriptions.

A provider adapter is responsible for signature verification and normalization
before calling the ledger.

## Media graph

`ContentAsset -> ContentProjection` preserves source asset ID and source version.
Derived content requires source provenance and is review-required by default.
Channel ranking is a decision aid that includes platform-dependency/policy cost;
it is never permission to publish.

## Revenue portfolio

The portfolio layer distinguishes active/passive/mixed streams and calculates:

- contribution margin;
- passive leverage ratio;
- positive-margin revenue-mode mix;
- HHI-like concentration by platform;
- review-only prune candidates for negative-margin or high-burden/trust-negative
  streams.

No metric triggers deletion or financial action by itself.

## Payments / paid accounts adapter boundary

Provider-specific payment code must live outside the governance kernel. For a
Stripe/Vercel adapter:

1. prefer hosted/standard payment primitives such as Checkout/Billing for paid
   accounts rather than rebuilding payment processing;
2. use restricted/scoped credentials where supported and keep secrets server
   side;
3. verify webhook signatures and make fulfillment idempotent;
4. never infer tax registration or legal obligations from code configuration;
5. keep entitlements separate from raw payment events;
6. route refunds, transfers, payouts, tax changes, major pricing changes and
   connected-account authority through explicit permissions;
7. pin/test provider versions and follow current provider guidance rather than
   copying stale snippets.

## Economic mutation tests

The current `world_model` supports bounded scenario calculations. They are not
forecasts. Meaningful strategies should eventually be attacked with scenarios
such as:

- platform reach -80%;
- CAC x3;
- churn x2;
- major customer loss;
- infrastructure cost x2;
- channel shutdown;
- refund spike;
- trust drop;
- compliance uncertainty increase.

The purpose is not to predict the future perfectly. It is to expose fragile
assumptions and missing observability before real-world scale.

## Regeneration ladder

| Level | Reconstructs | Evidence target |
|---|---|---|
| R0 | asset | content/tool functionality |
| R1 | channel | acquisition/distribution capability |
| R2 | offer/funnel | value delivery + conversion path |
| R3 | business model | sustainable exchange mechanism |
| R4 | generator/policy | candidate-generation capability |
| R5 | ecosystem | required value closure from `K_V*` |

R5 is accepted only relative to an explicit probe family and residual epsilon.

## Meta-evolution

A generator may create a child generator candidate, but cannot judge or promote
it. Persist a meta layer only when:

`verified_gain > complexity_debt + risk_debt`

Otherwise merge, simplify or prune it.

## Provider/deployment findings

The live Vercel inventory checked during this implementation currently maps to
other GitHub repositories, not this Value OS branch. No cross-repository deploy
was attempted. This remains fail-closed until repository-to-project identity is
explicit.

## Next bounded extensions

The kernel remains provider-neutral. High-value next modules are:

- `adapters/stripe` — verified webhook normalization into `EntitlementEvent`;
- `adapters/web` — paid capability surfaces and reversible experiments;
- `attribution` — uncertainty-aware revenue lineage without claiming causality;
- `treasury` — recommendation-only allocation before permissioned execution;
- `market_observability` — probes/identifiability for unmet-need hypotheses.

Each extension must remain subordinate to the same constitution, authority
envelope and proof receipts.
