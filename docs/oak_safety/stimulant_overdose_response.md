# OAK-SAFE — Stimulant Overdose Response Card

> **Scope:** harm-reduction and emergency-response note for stimulant exposure/overdose scenarios.  
> **Status:** safety documentation, not medical diagnosis, not dosing advice, not a substitute for poison control, emergency services, physician, pharmacist, or local clinical protocols.

## 0. Red-line rule

If a stimulant overdose is possible, treat it as a **time-sensitive medical-risk event**.

**Immediate action:** contact local poison control or emergency services. Do not wait for symptoms to become severe.

This document must never be used to normalize, optimize, test, or justify supratherapeutic stimulant use.

## 1. OAK triage model

### O — Observe

Record only operationally necessary facts:

- substance name, formulation, and approximate amount;
- time since ingestion/exposure;
- co-ingestions: alcohol, caffeine, decongestants, antidepressants, stimulants, recreational substances, supplements;
- symptoms: chest pain, palpitations, shortness of breath, fainting, agitation, confusion, hallucinations, severe headache, vomiting, fever, tremor, seizure;
- relevant known history only if needed for care: cardiac disease, hypertension, seizure history, pregnancy, prescribed medications.

### A — Act safely

- Call poison control / emergency services.
- Do not drive.
- Stay with the person.
- Keep medication bottle/package available for responders.
- Avoid alcohol, caffeine, other stimulants, strenuous exercise, overheating, and additional doses.
- Follow clinician or poison-control instructions.

### K — Kill-risk escalation

Escalate to emergency services immediately for:

- chest pain, severe palpitations, fainting, or severe shortness of breath;
- seizure, loss of consciousness, severe confusion, hallucinations, or uncontrollable agitation;
- high fever/hyperthermia, severe tremor, rigid muscles, or suspected rhabdomyolysis;
- very high blood pressure symptoms such as severe headache, visual changes, neurological deficit;
- mixed or unknown ingestion.

## 2. Mechanistic summary

Stimulant toxicity is not simply “more focus.” It is a possible transition from therapeutic modulation to systemic overload.

### Physical layer

Possible sympathetic overdrive:

- heart rate increase;
- blood pressure instability;
- heat generation / hyperthermia risk;
- arrhythmia risk;
- dehydration and collapse risk.

### Chemical layer

Amphetamine-class stimulants can increase monoaminergic signaling, especially norepinephrine and dopamine. Excessive exposure can saturate useful regulation and produce toxic excitation rather than improved cognition.

### Biological layer

The organism may enter a forced fight-or-flight state:

- cardiovascular strain;
- gastrointestinal stress;
- tremor and muscle overactivity;
- possible rhabdomyolysis under severe agitation/hyperthermia;
- kidney and thermal-risk cascades in severe cases.

### Neurological layer

The nervous system can move from attention support to dysregulation:

- anxiety/panic;
- agitation;
- insomnia;
- confusion;
- paranoia/hallucinations;
- seizures in severe toxicity.

## 3. Negative memory M−

Common unsafe failure modes to prevent:

1. **Weight normalization error:** assuming high body weight makes a large stimulant dose safe.
2. **Tolerance illusion:** assuming prior use prevents overdose.
3. **Wait-and-see delay:** delaying poison-control/emergency contact until severe symptoms.
4. **Stacking error:** adding caffeine, nicotine, decongestants, alcohol, antidepressants, or other stimulants.
5. **Public-dosing error:** publishing personalized dosing narratives as if they were safe guidance.
6. **Autonomous-medical-agent error:** allowing an AI or automation to make emergency medical decisions without human clinical escalation.

## 4. Canonical response template

When a user asks about possible stimulant overdose:

1. State that it can be dangerous.
2. Recommend poison control / emergency services immediately if already taken.
3. List red-flag symptoms.
4. Tell them not to drive and not to take additional substances.
5. Keep the explanation mechanistic but do not give optimization, abuse, or tolerance strategies.
6. Preserve privacy: do not publish personal health details into public repositories.

## 5. Integration hooks

Suggested future modules:

- `oak_safety_router.py`: classifies medical-risk prompts and routes to emergency-safe responses.
- `m_minus_medical_registry.yaml`: records unsafe reasoning patterns.
- `source_trust_ledger.yaml`: maps medical claims to official labels, poison-control pages, and clinical references.
- `red_flag_detector.py`: extracts escalation symptoms from user text.

## 6. OAK status

- **Medical authority:** external clinician / poison control / emergency services required.
- **AI status:** supportive safety explanation only.
- **Automation level:** L0-L1. No autonomous diagnosis, no autonomous dosing, no suppression of escalation.
- **Merge status:** should remain review-gated before inclusion in public canon.
