# Ω-UNC²-T — Incertitude de l’Incertitude de Tristan

Prototype OAK-safe pour transformer chaque claim, mesure, estimation ou décision en objet auditable :

```text
claim → U1 incertitude directe → U2 incertitude de l’incertitude → résidus → OAK-U²Gate → action robuste → M⁺/M⁻
```

## Rôle

Ω-UNC²-T est le moteur transversal anti-surconfiance du corpus Tristan. Il ne cherche pas seulement à donner une probabilité ou une marge d’erreur : il mesure la fiabilité de cette marge d’erreur.

Exemples de questions traitées :

- le ± annoncé est-il lui-même calibré ?
- le score de confiance vient-il d’une source, d’un modèle ou d’une intuition ?
- la certitude a-t-elle une demi-vie courte ?
- le coût d’erreur exige-t-il une vérification humaine ?
- quelle action reste robuste même si l’incertitude est mal estimée ?

## Hiérarchie U0–U5

| Niveau | Nom | Description |
|---|---|---|
| U0 | Objet | donnée, source, claim, mesure, prototype, théorie ou décision |
| U1 | Incertitude | bruit, manque de données, erreur de modèle, dérive, ambiguïté |
| U2 | Méta-incertitude | fiabilité de U1, calibration, stabilité, résidu de résidu |
| U3 | Méta-méta contrôlée | activée seulement si coût d’erreur ou irréversibilité élevé |
| U4 | Décision robuste | action qui reste bonne sous incertitude mal estimée |
| U5 | Mémoire évolutive | M⁺/M⁻ pour apprendre des surconfiances passées |

## Modules

```text
omega_unc2_t/
  u2_types.py       # dataclasses U2Claim, U2Vector, EvidencePacket
  scoring.py        # U1/U2/risk/maturity/priority/confidence-debt
  oak_gate.py       # OAK-U²Gate et statuts BLACK/RED/ORANGE/YELLOW/GREEN/BLUE/GOLD
  calibration.py    # ECE1, méta-ECE2, résidu de l’incertitude
  unknown_unknown.py# radar d’inconnus inconnus
```

## Exemple minimal

```python
from omega_unc2_t import U2Claim, oak_u2_score, oak_u2_gate

claim = U2Claim(
    claim="FFWT-HAC améliore la détection d’anomalies multiscales.",
    estimate=0.72,
    uncertainty_u1={"model": 0.42, "epistemic": 0.35, "decision": 0.50},
    meta_uncertainty_u2={"model_disagreement": 0.55, "residual_volatility": 0.62},
    evidence_strength=0.35,
    residual_score=0.40,
    decision_cost=0.70,
    reversibility=0.80,
)

score = oak_u2_score(claim)
status = oak_u2_gate(score)
print(score)
print(status.status, status.next_action)
```

## Règle OAK-safe

Aucune certitude ne monte sans : provenance, domaine de validité, calibration, historique de résidus, coût d’erreur, contre-hypothèse et mémoire négative.

## Intégrations prévues

- Ω-INFO²-T : provenance, fraîcheur, preuve, information sur l’information.
- Ω-CALIB-T : calibration des instruments et certificats numériques.
- Bayes-Tristan : probabilité hiérarchique avec incertitude de modèle.
- Rosette-Tristan : extraction PDF annotée par page/bbox/U1/U2.
- Ω-REV-T : revenus sans hype, validation par ventes réelles.
- Ω-MED-T : prudence clinique, données manquantes, clinicien humain.
- Ω-AUTO²-T : autonomie contrôlée par U2 et irréversibilité.
