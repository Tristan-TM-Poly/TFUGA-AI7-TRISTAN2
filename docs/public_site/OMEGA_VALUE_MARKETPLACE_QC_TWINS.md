# Ω-VALUE-MARKETPLACE-T × Ω-QC-GROUP-TWIN-T

## Objet

Étendre Tristan Web OS avec un coffre privé pour abonnés, un marché de téléchargements numériques payants dont le prix est borné par une **Value Receipt** vérifiable, et un registre de jumeaux numériques de groupes/organisations du Québec.

Cette extension est proof-first et fail-closed. Une interface qui ressemble à un paiement n'est pas considérée comme un paiement fonctionnel tant que les capacités serveur réelles ne sont pas configurées et testées.

## Invariants

- `Upload ≠ Publication`.
- `Uploaded ≠ Safe`.
- `Stored code ≠ Executed code`.
- `Generated price ≠ Proven value`.
- `Value score ≠ Human worth`.
- `Purchase ≠ Public URL`.
- `Collective twin ≠ Individual profile`.
- `Public information ≠ Unlimited reuse right`.
- `Group membership ≠ Inference target`.
- `Sensitive characteristic ≠ Permitted twin feature`.
- `Simulation/Twin ≠ Reality`.

## Upload pipeline

1. Subscriber/authentication gate.
2. Rights declaration and privacy declaration.
3. File classification.
4. Passive documents/media: candidate for private upload.
5. ZIP/archives/macros/active content: quarantine mandatory.
6. Executable binaries: blocked by default.
7. Malware/archive-bomb/content scan.
8. Hash + immutable provenance receipt.
9. Private object storage.
10. Optional extraction/indexing only in an isolated sandbox and never by executing uploaded code.

The browser may perform a preliminary classification, but the server must repeat every gate. Client metadata is never authoritative.

## Proof-carrying pricing

`ValueReceipt = f(evidence, utility, reproducibility, provenance, rights, uniqueness, freshness, buyer_validation)`

Hard gates require at minimum:

- measured-or-better evidence;
- sufficient provenance;
- explicit rights readiness;
- minimum reproducibility;
- at least one independent evidence receipt.

The current kernel emits a suggested CAD price plus a bounded floor/ceiling. Production checkout must recompute the receipt server-side and reject a client-provided price that differs from the server decision.

### Commercial rule

Price is a commercial decision constrained by evidence. It is not an objective measure of truth, moral value, social importance, or the worth of a person/group.

## Paid download pipeline

`asset -> safety gates -> verified ValueReceipt -> server price -> checkout -> payment confirmation -> entitlement ledger -> short-lived private download`

Revocation must be possible after refund, rights dispute, malware discovery, privacy incident, or asset withdrawal.

Recommended production components:

- identity/session provider;
- private object storage;
- malware + archive scanning worker;
- Stripe Checkout/Billing for subscription and one-time purchases;
- server-side entitlement ledger;
- tax configuration appropriate to the actual business status;
- signed short-lived download links or authenticated streaming;
- audit/evidence ledger.

## Québec Group Twin Registry

The registry is **generative**, not an assertion that every real Quebec group has already been enumerated. It defines families from which admissible twins can be instantiated with sources, observables, uncertainty, last verification time, and OAK gates.

Current families include territories/MRC, municipalities, education, research, health, public bodies, companies, cooperatives, nonprofits, associations, labour organizations, culture/media, sports, environment, innovation, civic/public institutions, Indigenous nations/organizations, and local communities.

### Privacy and governance gates

A collective twin must not:

- create a profile of a natural person;
- infer that a person belongs to a group;
- infer protected or sensitive characteristics;
- publish personal data because it happened to be uploaded;
- reduce small cohorts to re-identifiable aggregates.

For non-public collectives, use consent or sufficiently aggregated data. A default anti-reidentification threshold is represented in the kernel. For communities requiring data sovereignty or special governance, community governance/consent is a hard gate.

If a twin uses personal information, a privacy impact assessment and the legally required governance must occur before production use.

## Production capability gate

`LIVE_READY` requires all of:

- identity;
- private storage;
- malware scanning;
- payments;
- entitlement ledger;
- tax configuration.

If one is missing, production actions remain `FAIL_CLOSED`.

## API contract to implement

### `POST /api/marketplace/upload-ticket`

Input: authenticated subscriber, file manifest, rights/privacy declarations.

Output: short-lived private upload target + asset draft id, or HOLD/QUARANTINE.

### `POST /api/marketplace/value-receipt`

Input: asset id + evidence receipts.

Output: signed ValueReceipt and server price bounds.

### `POST /api/marketplace/checkout`

Input: authenticated buyer + asset id.

Server recomputes price; client never supplies authoritative amount.

Output: Stripe Checkout session.

### `POST /api/marketplace/download-ticket`

Input: authenticated buyer + asset id.

Server checks purchase/subscription entitlement, refund/revocation, safety, privacy, rights and ValueReceipt.

Output: short-lived private download target.

### `POST /api/qc-twins`

Input: admissible collective entity + provenance + source mode + observables.

Output: twin draft only if `groupTwinGate` passes.

## OAK acceptance tests

- executable upload blocked;
- ZIP upload quarantined;
- no upload without subscriber + rights + privacy declarations;
- provisional ValueReceipt cannot authorize a paid price;
- paid download denied without entitlement;
- refund/revocation denies future access;
- sensitive/person-level twin inference always HOLD;
- small aggregate cohorts are held when re-identification risk is material;
- production readiness remains fail-closed until all six capabilities are true.

## Deployment note

The current `apps/tristan-8fire-site` is a static proof-first web application. The new UI and kernel are integrated into that architecture. The production backend must be deployed as a server-authoritative API before setting `TRISTAN_MARKETPLACE_CAPABILITIES` to ready values.

For a Vercel deployment, private blob/object storage plus server routes and Stripe is a natural target, but exact provider selection is intentionally not hard-coded into the proof kernel.
