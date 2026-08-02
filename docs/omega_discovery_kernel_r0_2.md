# Ω-DISCOVERY-KERNEL-T∞ R0.2

## Closed-loop discovery at adaptive frontier scale

**Status:** executable software architecture, deterministic scale tests, OAK-safe dry-run generation, not scientific certification.

R0.2 converts the original eight-event proof of concept into a diversified discovery operating kernel capable of processing and planning tens of thousands of traceable additions without loading the complete graph into memory.

The central distinction is:

```text
control-plane source code
≠ generated event volume
≠ scientific evidence
≠ canonical knowledge
```

The source package remains compact enough to audit. Its tests exercise a much larger logical frontier:

```text
50,000 streamed discovery events
+
50,100 diversified GitHub logical additions
=
100,100 validated workflow additions per full R0.2 test cycle
```

These counts are finite experiments. They are not permanent ceilings.

---

# 1. Architecture

R0.2 unifies five existing systems:

```text
WikiForge / HyperKnowledge
        ↓
Ω-DISCOVERY-KERNEL-T∞
        ↓
Generator Discovery / MorphIR
        ↓
OAK transitions + M⁻ / M⁺
        ↓
Ω-SANS-PLAFOND dry-run planning
```

The kernel does not replace the specialized systems. It supplies a common identity, event, quantity, provenance and execution language between them.

## 1.1 Minimal closed loop

Every complete discovery subject may traverse the core loop:

```text
ObservationEvent
→ ClaimEvent
→ GeneratorCandidate
→ ExperimentSpec
→ ResultPacket
→ OAKTransition
→ MMinusRule
→ ActionProposal
```

This eight-event loop remains the minimum closure criterion.

## 1.2 Extensible Ω64 catalog

R0.2 adds 64 canonical event contracts organized into eight families:

1. ingestion and observation;
2. epistemic objects;
3. models and generators;
4. experiments and evidence production;
5. OAK governance;
6. positive and negative memory;
7. actions, publication and value routing;
8. operations, economics, safety and lifecycle.

A subject does not need all 64 events. The catalog provides typed extensions when the workflow requires them.

---

# 2. Ω64 event catalog

## 2.1 Ingestion and observation

```text
ObservationEvent
ImportEvent
NormalizationEvent
CalibrationEvent
SegmentationEvent
FeatureExtractionEvent
ProvenanceEvent
QualityGateEvent
```

These events preserve the difference between raw input and interpreted input.

### Required principle

```text
normalization never deletes the raw observation;
segmentation preserves source coordinates;
feature extraction produces candidates, not causal claims;
quality acceptance is not truth certification.
```

## 2.2 Epistemic objects

```text
DefinitionEvent
ClaimEvent
AssumptionEvent
EquationEvent
PredictionEvent
ContradictionEvent
ScopeRevisionEvent
RefutationEvent
```

A claim must remain atomic enough to have explicit assumptions, scope and failure conditions.

A contradiction is a review candidate until scope, protocol, units, uncertainty, dataset and timing have been compared.

A refutation is always scoped. It does not automatically invalidate every related theory.

## 2.3 Models and generators

```text
GeneratorCandidate
GeneratorFitEvent
ModelSelectionEvent
ReconstructionEvent
ForecastEvent
ResidualEvent
SyndromeEvent
ModelRejectedEvent
```

The model layer preserves the hierarchy:

```text
representation
→ reconstruction
→ held-out forecast
→ discriminating prediction
→ experimental validation
```

Each arrow requires additional evidence.

## 2.4 Experiments and evidence

```text
ExperimentSpec
SimulationRun
MeasurementRun
BaselineComparison
AblationRun
ReplicationEvent
SensitivityRun
ExperimentClosedEvent
```

A valid experiment contract includes:

```text
protocol;
inputs and outputs;
units;
uncertainty;
baseline;
metric;
success criterion;
failure criterion;
safety boundary;
rollback or compensation;
artifact hashes.
```

## 2.5 OAK governance

```text
OAKTransition
PromotionEvent
DemotionEvent
ApprovalEvent
RejectionEvent
QuarantineEvent
ArchiveEvent
RestorationEvent
```

Promotions are harder than demotions.

A promotion toward measured, canonical or certified status requires evidence ancestry appropriate to the target.

Irreversible publication, deployment or retirement remains human-approved.

## 2.6 Memory

```text
MMinusRule
MPlusRule
CounterexampleEvent
FailureContextEvent
AntiPatternEvent
LessonEvent
ConstraintEvent
MemoryPropagationEvent
```

M⁻ is not a failure log alone. It encodes:

```text
context;
metric;
baseline;
conditions;
prohibited inference;
reusable anti-error rule;
propagation targets;
next discriminating action.
```

M⁺ records positive patterns but never converts repeated internal success into universal truth.

## 2.7 Actions and value routing

```text
ActionProposal
TaskPlannedEvent
RollbackEvent
CompensationEvent
PublicationEvent
IPClassificationEvent
ProductHypothesisEvent
CustomerEvidenceEvent
```

The action layer separates:

```text
proposal
from approval;
approval from execution;
execution from outcome;
outcome from market validation.
```

## 2.8 Operations and lifecycle

```text
RevenueEvidenceEvent
CostEvidenceEvent
RiskAssessmentEvent
ComplianceEvent
DeploymentEvent
IncidentEvent
MaintenanceEvent
RetirementEvent
```

Revenue evidence must refer to an actual transaction record. A forecast is not revenue.

Compliance metadata does not replace professional legal, safety, privacy or regulatory review.

---

# 3. Universal identities

R0.2 introduces content-addressed identities of the form:

```text
urn:omega:<namespace>:<kind>:<local-id>:<version>:<digest>
```

The identity contract applies to:

```text
TheoryNode
KnowledgeCell
ClaimAtom
EvidenceRecord
MorphIR
GeneratorCandidate
ExperimentSpec
ResultPacket
Dataset
Commit
PullRequest
Instrument
ProductHypothesis
IPClassification
```

Each identity can include:

```yaml
universal_id:
kind:
namespace:
local_id:
version:
content_hash:
parent_ids:
source_ids:
supersedes:
aliases:
repository_commit:
valid_from:
valid_until:
oak_status:
metadata:
```

## 3.1 Identity does not imply equivalence

Two records can share a label while representing different concepts.

Aliases are typed as:

```text
exact_alias
probable_alias
historical_name
abbreviation
translation
overlap
specialization
generalization
not_equivalent
```

A content hash establishes byte-level content identity for the canonical representation used by the kernel. It does not establish semantic truth.

## 3.2 Revision graph

A revision preserves:

```text
parent identity;
superseded identity;
new content hash;
repository commit;
new OAK status;
validity dates;
residual differences.
```

The history is append-only. Older beliefs are not silently rewritten.

---

# 4. Quantities, units and uncertainty

Scientific events should not carry naked floating-point values when units or uncertainty matter.

R0.2 introduces:

```text
UnitDefinition
CalibrationReference
Quantity
QuantityVector
```

A quantity contains:

```yaml
value:
unit:
standard_uncertainty:
distribution:
coverage_factor:
calibration_id:
validity_domain:
provenance:
status:
```

The compact unit registry covers common dimensions used by the current prototypes:

```text
dimensionless
length
time
frequency
temperature
pressure
energy
power
voltage
current
charge
amount
concentration
mass
angle
wavenumber
detector counts
arbitrary intensity
pixel
information
currency
```

## 4.1 OAK boundary

The registry supports deterministic software contracts. It does not replace:

```text
VIM;
GUM uncertainty evaluation;
ISO/IEC 17025;
traceability chains;
domain-specific calibration;
correlated uncertainty analysis;
professional metrology review.
```

---

# 5. Disk-backed streaming frontier

The in-memory ledger is suitable for small, inspectable demonstrations.

The streaming ledger is designed for larger frontiers.

## 5.1 Storage architecture

```text
immutable JSONL shards
+
SQLite event and parent index
+
checkpoint.json
+
telemetry.json
+
manifest.json
+
M⁻ ledger
+
quarantine ledger
```

The full graph is never required in memory.

## 5.2 Adaptive behavior

The frontier uses:

```text
adaptive shard byte budgets;
WAL-mode SQLite indexing;
content/event ID deduplication;
periodic commits;
periodic checkpoints;
resume support;
disk-reserve backpressure;
quarantine on invalid records;
telemetry for throughput and saturation;
ledger digest accumulation.
```

There is no permanent `max_total_events` field.

A run remains bounded by:

```text
finite source workload;
available storage;
compute and wall-clock budget;
quality and validation capacity;
safety and legal constraints;
rollback requirements;
external provider quotas.
```

## 5.3 50,000-event OAKBench

The deterministic frontier test writes:

```text
6,250 complete subjects
× 8 core events
= 50,000 events
```

It verifies:

```text
all event hashes;
parent existence;
chronological ordering;
subject isolation;
complete core masks;
50,000 SQLite index rows;
6,250 subject rows;
6,250 M⁻ records;
multiple JSONL shards;
checkpoint completion;
zero orphan references;
resume deduplication.
```

The generated events are workflow scale records, not scientific evidence.

---

# 6. Diversified benchmark registry

R0.2 includes 36 benchmark families spanning more than 30 domains.

## 6.1 Spectroscopy and analytical science

```text
Raman peak morphology
FTIR band morphology
XRD peak and phase analysis
NMR line shape
UV-visible absorption
fluorescence lifetime
mass spectrometry isotope envelopes
chromatographic elution
```

## 6.2 Electrochemistry, energy and devices

```text
electrochemical impedance
battery degradation
microgrid dispatch
thermoelectric conversion
metasurface optics
temporal photonic crystals
MEMS resonators
```

## 6.3 Materials and natural science

```text
EBSD orientation fields
stress-strain constitutive models
mass-action kinetics
Michaelis-Menten kinetics
Belousov-Zhabotinsky dynamics
reduced carbon cycles
predator-prey ecology
```

## 6.4 Computation, control and information

```text
instrument calibration
time-series drift
multiscale anomaly detection
image deconvolution
local linearization
Koopman/DMD
LQR/MPC control
error-correction syndromes
software CI regression
```

## 6.5 Knowledge, legal, product and repository systems

```text
epistemic density
legal/IP gates
product-market evidence
document-code divergence
repository supply-chain analysis
```

Each family defines:

```yaml
family_id:
domain:
purpose:
observables:
continuous_generators:
discrete_events:
baselines:
metrics:
noise_models:
units:
failure_conditions:
safety_boundary:
```

The registry is a benchmark specification library. It does not contain measured scientific outcomes.

---

# 7. 50,100-addition knowledge frontier

The factory emits a heterogeneous addition stream:

| Kind | Count |
|---|---:|
| Knowledge cells | 100 |
| Claims | 1,000 |
| Evidence contracts | 5,000 |
| Experiment specifications | 1,000 |
| Result contracts | 10,000 |
| Action proposals | 10,000 |
| M⁻ rules | 10,000 |
| Universal identities | 1,000 |
| Benchmark cases | 12,000 |
| **Total** | **50,100** |

## 7.1 Why generated contracts matter

The generated records are not automatically promoted to evidence.

They serve as:

```text
schema stress tests;
workflow fixtures;
indexing and sharding tests;
coverage targets;
placeholder queues for real external evidence;
anti-false-density demonstrations.
```

Each placeholder states that it must be replaced by real provenance, data, code, tests, baselines or measurements before promotion.

## 7.2 Ω-SANS-PLAFOND integration

The factory streams additions into `GitHubDryRunPlanner`.

The planner generates:

```text
shards/
plan-index.sqlite3
tree.jsonl
commit-plan.jsonl
rollback.jsonl
checkpoint.json
manifest.json
semantic-diff.json
oak-report.json
benchmark-registry.json
knowledge-frontier-summary.json
```

It performs zero GitHub mutations.

Each future branch, stage, commit, push and pull request remains a separately authorized phase.

---

# 8. Command line

## 8.1 Raman closed loop

```bash
python -m omega_discovery_kernel_t demo \
  --output-dir generated/omega_discovery_kernel_t/raman-r0-2
```

## 8.2 Event catalog

```bash
python -m omega_discovery_kernel_t catalog \
  --output generated/omega_discovery_kernel_t/event-catalog-r0-2.json
```

## 8.3 50,000-event frontier

```bash
python -m omega_discovery_kernel_t frontier \
  --events 50000 \
  --namespaces 32 \
  --checkpoint-interval 5000 \
  --commit-interval 1000 \
  --output-dir generated/omega_discovery_kernel_t/frontier-50k-r0-2
```

## 8.4 50,100-addition plan

```bash
python -m omega_discovery_kernel_t plan-additions \
  --cells 100 \
  --claims-per-cell 10 \
  --evidence-per-claim 5 \
  --experiments-per-claim 1 \
  --results-per-experiment 10 \
  --actions-per-result 1 \
  --memory-rules-per-result 1 \
  --identities-per-claim 1 \
  --benchmark-cases 12000 \
  --output-dir generated/omega_discovery_kernel_t/additions-50100-r0-2
```

---

# 9. Metrics

## 9.1 Event-frontier metrics

```text
accepted_events
duplicate_events
rejected_events
bytes_written
shards_closed
checkpoints_written
SQLite commits
write seconds
validation seconds
events per second
bytes per second
subject count
event-type counts
closed-loop coverage
integrity findings
```

## 9.2 Addition-frontier metrics

```text
raw records
unique additions
duplicates
invalid records
shards
payload bytes
namespaces
approval-required additions
logical additions by kind
rollback entries
commit-plan entries
```

## 9.3 Epistemic metrics still required

Future releases should add:

```text
real-source replacement rate;
external-evidence coverage;
independent replication coverage;
measurement coverage;
baseline fairness audit;
stale-status ratio;
negative-memory propagation rate;
canonical density;
proof density;
customer-evidence coverage;
value delivered per validated claim.
```

---

# 10. Anti-false-density rules

## Rule 1

```text
A generated record is not evidence merely because it validates against a schema.
```

## Rule 2

```text
A complete event chain proves workflow completion, not causal truth.
```

## Rule 3

```text
More nodes, events or lines do not imply more knowledge.
```

## Rule 4

```text
Internal consistency among Tristan modules does not replace external baselines.
```

## Rule 5

```text
A result is limited to its protocol, data, metric, uncertainty and validity domain.
```

## Rule 6

```text
A failed result should generate scoped M⁻, not disappear and not become a universal refutation.
```

## Rule 7

```text
An irreversible action requires accountable human approval.
```

## Rule 8

```text
The growth frontier is adaptive, but canonical promotion remains intentionally difficult.
```

---

# 11. Current validation status

R0.2 validates software and workflow properties:

```text
Python compilation;
full pytest suite;
50,000-event streaming frontier;
50,100-addition GitHub planning frontier;
Ω64 uniqueness and family coverage;
identity determinism and revision links;
unit conversion and uncertainty propagation;
JSON schema validity;
claims validation;
Reactor and propagation checks;
Bayes-Tristan scoring;
OAK/CVCD reports;
guarded auto-genesis.
```

It does not establish:

```text
scientific superiority;
causal discovery;
physical validity;
safety certification;
legal compliance;
patentability;
product-market fit;
revenue repeatability.
```

---

# 12. Next frontiers

## R0.3 — Real evidence replacement

```text
replace generated evidence contracts with exact locators and hashes;
ingest public Raman, FTIR, XRD and calibration datasets;
add matched SciPy and domain baselines;
record held-out predictions and uncertainty coverage;
create automatic KnowledgeCell revisions from ResultPacket events.
```

## R0.4 — Incremental repository metabolism

```text
convert commits, tests and benchmark runs into events;
detect stale claims after code changes;
propagate M⁻ into affected cells;
route differential CI from changed hyperedges;
maintain append-only temporal canon snapshots.
```

## R0.5 — Million-event architecture test

```text
1,000,000 streamed events;
multiple producer processes;
partitioned SQLite or alternate index backends;
checkpoint recovery after forced interruption;
shard compaction without history loss;
validation sampling plus deterministic deep audits;
resource and energy telemetry;
M⁻ records for every observed saturation.
```

## R1.0 — External discovery demonstration

A release candidate requires at least one end-to-end external demonstration:

```text
public dataset;
multiple hypotheses;
matched baselines;
held-out prediction;
calibrated uncertainty;
independent reproduction;
failed hypothesis demotion;
M⁻ propagation;
measured improvement in audit time, predictive quality or experiment selection.
```

---

# 13. Final OAK boundary

Ω-DISCOVERY-KERNEL-T∞ R0.2 is now a substantial execution and scale architecture.

Its strongest verified result is not a new scientific law. It is the ability to:

```text
represent a closed discovery loop;
apply fail-closed event contracts;
stream 50,000 events;
plan 50,100 diversified additions;
preserve provenance, hashes, units, uncertainty and rollback;
route failures into reusable negative memory;
scale without an arbitrary permanent total-count ceiling.
```

The next revolution must come from replacing generated contracts with external evidence and demonstrating that the complete loop makes a real scientific or engineering decision better than explicit baselines.
