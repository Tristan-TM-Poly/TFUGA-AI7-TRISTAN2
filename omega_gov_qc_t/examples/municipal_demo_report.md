# Municipalité-OAK — Demo Report

Status: example / non authoritative

> This example demonstrates report structure only. It is not an official assessment and uses placeholder entities.

## 1. Scope

Municipal public-service overview using registered public sources, graph nodes, evidence items and OAKGate checks.

## 2. Graph summary

- Municipality node: `municipality:demo`
- Region node: `region:demo`
- Service nodes: water, roads, permits, public communications
- Risk nodes: data freshness, missing metadata, unclear ownership

## 3. Signals

### Signal A — Data freshness review

Some datasets may need a freshness check before being used in a dashboard.

Status: signal

Required review:

- confirm update frequency ;
- confirm source owner ;
- confirm permitted reuse ;
- add retrieved_at timestamp.

### Signal B — Service-friction review

Some public-service pages may require simplification if citizens must consult multiple pages for one journey.

Status: hypothesis

Required review:

- map citizen journey ;
- identify repeated fields ;
- document language complexity ;
- ask human service owner to validate.

## 4. OAKGate

Deployment must remain blocked or internal-only if any of the following is missing:

- authorized source ;
- source date ;
- privacy assessment ;
- human owner ;
- explanation of limitations.

## 5. Recommendations

1. Build a source registry first.
2. Use open/public data for the demo.
3. Generate a graph quality report.
4. Produce a plain-language summary.
5. Keep all high-impact actions under human authority.

## 6. M- memory

- Do not publish a score without source context.
- Do not treat missing data as proof of poor performance.
- Do not infer intent from administrative delay.
- Do not mix internal and public data without explicit governance.
