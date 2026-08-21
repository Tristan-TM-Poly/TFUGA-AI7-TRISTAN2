# Ω-MANAGEMENT-T∞ R0.1 — Governed Capability Management

## Mission

Replace weak management proxies such as visible hours, meeting volume, message volume, and manager presence with an evidence-oriented operating model centered on verified outcomes, autonomy, resilience, decision quality, capability growth, friction, dependency, burnout risk, and management cost.

The core doctrine is:

```text
Manage people less as monitored activity.
Engineer conditions, capabilities, authority boundaries and evidence loops instead.
```

## Canonical loop

```text
Intent
→ WorldState
→ ResidualField
→ CandidateInterventions
→ Authority/Risk/Reversibility gates
→ Ranked recommendation
→ Human/platform-authorized action
→ ManagementReceipt
→ Outcome observation
→ Learning / M+ / M-
```

## Hard laws

```text
Presence != Leadership
HoursWorked != VerifiedOutcome
Activity != Value
ManagerVisibility != Commitment
Recommendation != Authority
CallerDeclaredAuthority != RealWorldAuthority
SoftwarePASS != OrganizationalEffectiveness
Correlation != Causality
LocalPASS != GlobalPASS
HighScore != PermissionToAct
```

## Core measures

### Leadership value

R0.1 uses a guarded local index:

```text
(VerifiedOutcome + Autonomy + Resilience + DecisionQuality + CapabilityGrowth)
----------------------------------------------------------------------------
1 + Friction + LeaderDependency + BurnoutRisk + ManagementCost
```

This is a decision-support index, not a universal personnel score.

### Leader Absence Test

```text
AbsenceResilience = PerformanceWithoutLeader / NormalPerformance
```

The test asks whether the organization remains capable when direct managerial intervention is removed. A high result does not imply the leader is unnecessary; it can indicate successful delegation, documentation, architecture, and capability transfer.

### Proxy Gap

When a weak proxy is used in place of a direct outcome measure, estimate the evidential gap between their outcome relevance and confidence. A large gap is a trigger to reduce reliance on the proxy and seek direct evidence.

## Event-driven management

Prefer intervention on meaningful residuals over calendar-driven supervision. Candidate triggers include sustained blockers, risk growth, authority ambiguity, evidence gaps, decision latency, overload, dependency concentration, or missed verified outcomes.

## Management metabolism

The long-term target is lower required management intervention per unit of verified value while maintaining or improving safety, resilience, fairness, learning, and accountability.

```text
VerifiedCapabilityCreated × Autonomy × Resilience
------------------------------------------------
RequiredLeaderIntervention + Friction + Risk
```

## OAK boundary

This package does not infer employee intent, commitment, protected characteristics, legal compliance, causal leadership quality, or organizational truth. Metrics must never become hidden automated disciplinary gates. High-impact personnel decisions require appropriate human judgment, policy, evidence, and legal/HR review where applicable.

## R0.1 software surface

- `ManagementSignal`
- `ManagementState`
- `InterventionCandidate`
- `ManagementReceipt`
- `proxy_gap()`
- `absence_resilience()`
- `leadership_value()`
- `prioritize_interventions()`

R0.1 is intentionally small: it establishes the semantic and safety kernel before any integration with communications, calendars, HR systems, project systems, GitHub, CRM, finance, or external actuation.
