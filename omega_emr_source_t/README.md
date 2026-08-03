# Ω-EMR-SOURCE-T∞ R0.1

`omega_emr_source_t` is an analysis-only inverse-design kernel for selecting
physical electromagnetic-emission mechanism families from a multidimensional
spectrum target.

It models the source grammar:

```text
Driver -> Transducer -> Resonator/Selector -> Guide/Aperture
       -> Modulator -> Stabilizer -> Detector -> SafetyGate
```

## R0.1 capabilities

- classifies frequency, wavelength, photon energy and functional spectral region;
- searches an atlas of 20 established physical emission-mechanism families;
- ranks compatible mechanisms deterministically;
- distinguishes recommended, conditional and rejected routes;
- emits architecture, metrology, uncertainty and safety-control plans;
- permits simulation of sensitive regimes while blocking unauthorized physical work;
- produces JSON and Markdown evidence bundles;
- audits each plan with OAK checks and explicit epistemic status.

The score is a routing heuristic, not a probability, measured efficiency or
claim that one device is superior.

## Safety boundary

The package does not operate hardware and does not emit fabrication recipes.
Ionizing-capable, radioactive, accelerator, high-power RF, high-voltage, strong
magnetic-field, UV and laser routes are conservatively escalated to simulation,
certified modules or authorized institutional facilities.

`allow_radiating_output=false` is the default. RF plans therefore prefer a
simulation, shielded environment or matched load until explicit authorization
and jurisdiction-specific review exist.

## CLI

```bash
omega-emr-source classify 5e14
omega-emr-source atlas semiconductor
omega-emr-source plan target.json --output-dir generated/omega_emr_source_t
```

Example target:

```json
{
  "center_frequency_hz": 500000000000000.0,
  "bandwidth_hz": 20000000000000.0,
  "power_w": 0.001,
  "coherence": "low",
  "environment": "shielded_lab",
  "max_prototype_tier": "low_power_benchtop"
}
```

Outputs:

```text
source-plan.json
oak-report.json
report.md
```

## OAK promotion path

```text
fertile concept
-> formal target
-> deterministic source-family plan
-> simulation against baseline
-> calibrated low-risk measurement
-> uncertainty and residual analysis
-> reviewed prototype status
```

No source becomes canonical merely because it is named, ranked or simulated.
