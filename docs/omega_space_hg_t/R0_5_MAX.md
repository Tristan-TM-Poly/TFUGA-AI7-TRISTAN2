# Ω-SPACE-HG-T∞ R0.5 MAX — Constellations and Mycelial Operations

## Scope

R0.5 extends the single-spacecraft stack to deterministic Walker constellations,
sampled ground coverage, intersatellite line of sight, connected components,
greedy distributed task allocation, function migration and failed-slot
replenishment records.

It is research software. It is not an operational coverage guarantee, licensed
network design, conjunction analysis, collision-avoidance system, servicing
controller or launch/replenishment trajectory product.

## Walker generator

The generator constructs a Walker-delta-style circular constellation from:

- total satellites;
- number of planes;
- phasing index;
- altitude and inclination;
- central-body radius and gravitational parameter;
- per-node abstract capacity.

Every satellite retains a deterministic plane, slot, RAAN, phase and mean
motion. The first OAK gate verifies 24 unique satellites in six planes.

## Sampled coverage

Ground targets carry latitude, longitude, minimum elevation and priority.
Coverage is sampled over a finite horizon using a rotating spherical Earth.
Reports preserve visible fraction and maximum sampled outage for each target,
plus a weighted aggregate.

The canonical OAK comparison verifies that the declared 24-satellite fixture is
not worse than its 12-satellite counterpart on the same finite target/time grid.
This is a regression invariant, not a universal theorem that adding any
satellite always improves every metric.

## Intersatellite network

Links require both:

1. Euclidean separation below a declared maximum;
2. a line segment that clears the central body by a declared margin.

The graph is undirected and deterministic. Connected components expose network
fragmentation rather than silently assuming all spacecraft can communicate.

## Distributed tasks

Observation tasks carry target, epoch, demand and priority. A deterministic
greedy allocator ranks visible spacecraft by elevation and remaining scalar
capacity. Unassigned work remains explicit.

The allocator does not yet include slew, momentum, power, storage, downlink,
thermal, interference, precedence or mixed-integer scheduling constraints.

## Mycelial function migration

Functions are assigned to surviving nodes under declared scalar capacities.
Failed nodes are removed before allocation. The report preserves assignments,
unassigned functions and residual capacity. A `graceful=false` result is a
first-class negative witness.

## Degradation and replenishment

The canonical degradation fixture removes three spacecraft, recomputes coverage
and network state, and produces one replacement record per failed plane/slot.
The replacement plan records the desired slot only; it does not design a launch,
transfer, insertion, collision-safe phasing or regulatory mission.

## OAKBench gates

R0.5 verifies:

1. Walker plane/slot cardinality and unique identifiers;
2. finite sampled coverage monotonicity for the canonical 12/24 comparison;
3. a largest intersatellite component containing at least 75% of nodes;
4. nonzero coverage and three replacement records after three failures;
5. exact replay of coverage, network, task and migration outputs;
6. explicit unassigned functions under insufficient surviving capacity;
7. absence of proof, validation, qualification, operational coverage,
   collision-safety or autonomous-servicing claims.

## Commands

```bash
omega-space-hg-r05 manifest
omega-space-hg-r05 simulate --duration-hours 24 --step-s 120
omega-space-hg-r05 simulate --fail sat-p00-s00 --fail sat-p01-s00
omega-space-hg-r05 oak
```

## M-minus registry

- `M⁻-SPACE-R05-001`: sampled coverage can miss short transitions.
- `M⁻-SPACE-R05-002`: spherical circular geometry omits perturbations and
  navigation uncertainty.
- `M⁻-SPACE-R05-003`: range plus body clearance is not a complete RF/optical
  intersatellite link model.
- `M⁻-SPACE-R05-004`: greedy assignment can be globally suboptimal.
- `M⁻-SPACE-R05-005`: scalar capacity hides software, timing, security and
  interface incompatibilities.
- `M⁻-SPACE-R05-006`: a replacement slot is not a safe deployment plan.
- `M⁻-SPACE-R05-007`: graceful degradation in one fixture does not certify a
  constellation architecture.

## Next frontier

R0.6 should make requirements, interfaces, evidence, provenance, uncertainty,
verification method, cost, schedule, TRL, configuration and semantic diff
first-class hypergraph objects, producing a proof-carrying digital twin.
