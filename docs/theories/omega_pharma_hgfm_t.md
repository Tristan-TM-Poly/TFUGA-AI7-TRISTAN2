# Ω-PHARMA-HGFM-T
## Pharmacologie Hypergraphique Fractale Mycélienne de Tristan

> **Status:** OAK-safe research architecture.  
> **Hard boundary:** not medical advice, not dosing guidance, not self-experimentation guidance, not a replacement for poison control, emergency services, a physician, or a pharmacist.

## 0. OAK lock

Ω-PHARMA-HGFM-T models how molecules perturb a living organism across chemistry, physiology, neuroscience, psychology, time, context, and uncertainty.

It must never be used to optimize risky substance use, justify supratherapeutic dosing, bypass a prescription, normalize overdose, or automate medical decisions.

Canonical law:

```math
\boxed{\text{Pharmacology-safe} = \text{mechanism} + \text{time} + \text{context} + \text{uncertainty} + \text{OAK} + \text{qualified medical human}}
```

Negative law:

```math
\boxed{\text{No Tristan theory may transform a risky substance into an optimization game.}}
```

## 1. Fundamental axiom

A molecule is not a single effect.

```math
M \rightarrow A(t) \rightarrow C(t) \rightarrow S(t) \rightarrow R(t)
```

Where:

- `M` = molecule / formulation / exposure;
- `A(t)` = absorption, distribution, conversion, metabolism, elimination;
- `C(t)` = active concentration and metabolites;
- `S(t)` = biological signal;
- `R(t)` = multi-system response: useful, neutral, toxic, unstable, or unknown.

Therefore:

```math
\text{Effect} = f(\text{molecule}, \text{dose}, \text{time}, \text{body}, \text{brain}, \text{context}, \text{uncertainty})
```

No dose can be understood from body weight alone.

## 2. Body as pharmacological hypergraph

```math
B(t) = (V_B, E_B, W_B, U_B)
```

- `V_B`: organs, tissues, cells, receptors, transporters, enzymes, neural circuits;
- `E_B`: blood flows, endocrine loops, neural loops, immune loops, thermal loops;
- `W_B`: interaction weights, sensitivity, tolerance, genetics, health state;
- `U_B`: uncertainty, unknown interactions, measurement error, hidden vulnerabilities.

A molecule does not strike one isolated point. It traverses a living network.

## 3. Stability-basin principle

Any pharmacological exposure can be mapped to three conceptual zones:

```math
Z_1 = \text{sub-active / insufficient}
```

```math
Z_2 = \text{therapeutic or functional basin}
```

```math
Z_3 = \text{unstable or toxic basin}
```

Transitions can be nonlinear:

```math
\Delta \text{small dose} \Rightarrow \Delta \text{large risk}
```

especially when several loops couple:

```math
\text{heart} + \text{temperature} + \text{brain} + \text{sleep} + \text{co-ingestions}
```

## 4. Tristan law of coupled toxicity

Toxicity is not merely “too much molecule.” Toxicity is a coupled instability:

```math
T_{\Omega}(t)=
R_{cardio}(t)
\otimes R_{thermal}(t)
\otimes R_{neuro}(t)
\otimes R_{psych}(t)
\otimes R_{metabolic}(t)
\otimes U(t)
```

A single elevated channel may sometimes be compensated. Several elevated channels can create nonlinear risk.

Danger loop:

```text
stimulation -> agitation -> heat -> confusion -> more agitation -> higher thermal/cardiac/neurological risk
```

## 5. LOG/EXP pharmacology

### LOG pharmacology

Compress a drug event into invariants:

```math
LOG(M)=\{\text{class},\text{target},\text{duration},\text{conversion},\text{window},\text{risks},\text{interactions},\text{uncertainty}\}
```

Example stimulant scaffold:

```text
prodrug or stimulant exposure
-> active compound / metabolites
-> monoamine or autonomic perturbation
-> central + peripheral response
-> possible therapeutic basin or toxicity basin
```

### EXP pharmacology

Decompress invariants into possible system effects:

```math
EXP(LOG(M))=\{\text{attention},\text{appetite},\text{sleep},\text{blood pressure},\text{heart rhythm},\text{mood},\text{temperature},\text{risk}\}
```

OAK rule:

```math
EXP \neq \text{permission to self-experiment}
```

EXP exists to understand, prevent harm, and escalate safely.

## 6. Useful neurochemical threshold theory

The brain does not want maximum signal. It wants calibrated signal.

```math
Performance = f(\text{useful signal} - \text{noise} - \text{stress})
```

At an adapted therapeutic level:

```math
\text{useful signal} > \text{noise}
```

At excessive exposure:

```math
\text{noise} + \text{stress} + \text{disorganization} > \text{useful signal}
```

Canonical axiom:

```math
\text{stronger} \neq \text{smarter}
```

```math
\text{more stimulant} \neq \text{more productive}
```

Performance comes from a basin of coherence, not saturation.

## 7. Pharmacological safety tensor

Every exposure analysis should be represented as:

```math
\mathcal{P}_{safe} = [D,T,C,I,O,R,U,A]
```

- `D`: prescribed dose, taken dose, cumulative dose;
- `T`: time since exposure, expected duration, tail effects;
- `C`: context: sleep, heat, stress, food, hydration;
- `I`: interactions: alcohol, caffeine, nicotine, medication, recreational drugs, supplements;
- `O`: vulnerable organs/systems: heart, brain, liver, kidney, thermal system;
- `R`: risks: cardiovascular, neurological, psychiatric, digestive, thermal;
- `U`: unknowns;
- `A`: safest next action.

The output must not be an unsupervised dosing recommendation. The output is one of:

```text
pharmacist / prescriber / poison control / emergency services / clinician-supervised monitoring
```

depending on risk.

## 8. OAK-Pharma Gate

### Gate 1 — Reality

Is the question theoretical, a real ingestion, a possible overdose, a drug interaction, or a medication error?

### Gate 2 — Severity

Are there cardiac, neurological, psychiatric, respiratory, thermal, or unknown-risk signals?

### Gate 3 — Safe action

For real overdose or medication error:

```text
AI -> poison control / emergency services / physician / pharmacist
```

The AI does not replace the medical system.

### Gate 4 — Negative memory

Every unsafe reasoning pattern becomes an anti-pattern in M−.

## 9. M− pharmacology registry

Core unsafe patterns:

1. **Body-weight normalization error:** assuming high body weight makes high exposure safe.
2. **Tolerance illusion:** assuming prior use prevents overdose.
3. **Performance fallacy:** confusing stimulation with intelligence.
4. **Linearity fallacy:** assuming 4x dose means only 4x effect.
5. **Stacking error:** mixing caffeine, nicotine, alcohol, decongestants, antidepressants, recreational substances, or other stimulants.
6. **Wait-and-see delay:** waiting for severe symptoms before contacting poison control.
7. **Autonomous-medical-agent error:** allowing AI automation to make emergency medical decisions.
8. **Public-health-detail leakage:** committing personal medical details into public repositories.

## 10. Pharmacological phase transitions

A substance can trigger a phase transition:

```text
modulation -> overload -> disorganization -> crisis
```

For stimulant-like systems:

```text
focus -> jitter -> panic -> confusion -> seizure/cardiac/thermal risk
```

Critical threshold:

```math
\theta = \{\text{genetics},\text{heart},\text{sleep},\text{stress},\text{heat},\text{interactions},\text{dose},\text{time},\text{history}\}
```

The threshold is not universal.

## 11. Mother equation

```math
\frac{dB}{dt}=F(B,M,t,C)-G(B,t)+\epsilon
```

- `B`: biological state;
- `M`: molecule/exposure;
- `C`: context;
- `F`: pharmacological forcing;
- `G`: regulation/recovery;
- `ε`: uncertainty, noise, idiosyncrasy.

Risk:

```math
Risk(t)=\sigma\left(
\alpha_1R_{cardio}
+\alpha_2R_{neuro}
+\alpha_3R_{thermal}
+\alpha_4R_{psych}
+\alpha_5R_{interaction}
+\alpha_6U
\right)
```

If:

```math
Risk(t)>\tau_{OAK}
```

then:

```text
response = medical escalation
```

## 12. Canonical definition

Ω-PHARMA-HGFM-T is the theory that every psychoactive or physiological substance should be modeled as a multi-scale hypergraphic perturbation moving through body, brain, time, and context; its useful effect appears only inside a verified stability basin, while toxicity appears as a phase transition where cardiac, thermal, neurological, psychological, metabolic, interaction, and uncertainty loops couple beyond regulatory capacity.

## 13. Implementation targets

- `oak_medical_safety_router.py`: classify medical-risk prompts and return safe escalation frames.
- `m_minus_pharma.yaml`: registry of unsafe pharmacological reasoning patterns.
- `source_trust_ledger.yaml`: official-source mapping for pharmacology claims.
- `red_flag_detector.py`: detect emergency red flags in user text.
- `pharma_hypergraph_schema.json`: nodes/edges for substance, route, time, symptoms, context, actions.

## 14. Automation level

- Allowed: education, risk framing, source organization, emergency routing language, clinician-question preparation.
- Forbidden: autonomous diagnosis, dose planning, self-experimentation optimization, illegal substance guidance, delaying escalation, public exposure of private health details.

Default automation level: **L0-L1 only** for medical-risk contexts.
