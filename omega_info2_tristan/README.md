# Ω-INFO²-T — Théorie de l’Information de l’Information de Tristan

**Ω-INFO²-T** formalise la méta-information comme la couche qui décrit, certifie, compresse, contextualise, pondère, relie et transforme l’information elle-même.

Une donnée brute ne suffit jamais. Toute information utile doit être accompagnée de sa source, sa date, sa provenance, son incertitude, sa preuve, ses contradictions, sa demi-vie, ses risques, sa licence/IP, son statut OAK et son action recommandée.

```text
Donnée brute → Information → Information² → Bayes-Tristan → CVCD → OAK → Action → Mémoire M⁺/M⁻ → Canon
```

## Objectif du package

Ce dossier est un MVP logiciel pour transformer des objets informationnels en objets évaluables :

- `InfoObject` : unité canonique d’information augmentée.
- `Info2Tensor` / `InfoScores` : scores vérité/utilité/fertilité/testabilité/risque/fraîcheur/IP/compression.
- `BayesTristanUpdater` : mise à jour vectorielle vérité/utilité/fertilité/testabilité/sûreté/rentabilité/nouveauté.
- `CVCDCompressor` : extraction conservative d’invariants et conservation des résidus.
- `MMinusRegistry` : mémoire négative anti-erreur, JSONL et append-only.
- `SourceTrustKernel` : score de fiabilité d’une source.
- `OAKInfoGate` : validation avant canonisation.
- `InfoRouter` : routage vers archive, test, prototype, brevet, M⁻ ou canon.
- `Info2Graph` : hypergraphe claim-source-evidence-residue-action.
- `InfoHalfLife` : estimation d’obsolescence informationnelle.

## Installation locale

```bash
cd omega_info2_tristan
python -m pip install -e . pytest
python -m pytest
```

Le code utilise uniquement la bibliothèque standard Python pour le noyau afin de rester robuste, portable et zéro-friction.

## Exemple rapide

```python
from omega_info2 import (
    BayesTristanUpdater,
    CVCDCompressor,
    EvidenceVector,
    InfoObject,
    InfoScores,
    MMinusRegistry,
    OAKInfoGate,
    route_information,
)

obj = InfoObject.example()
obj.scores = InfoScores(truth=0.55, utility=0.91, fertility=0.86, testability=0.80, risk=0.18, source_trust=0.70)

BayesTristanUpdater().update_info_object(
    obj,
    [EvidenceVector(label="reproducible benchmark", truth_lr=2.5, utility_lr=1.4, source="benchmark:001")],
)
CVCDCompressor().compress_info_object(obj)
report = OAKInfoGate().evaluate(obj)
route = route_information(obj)

m_minus = MMinusRegistry()
m_minus.extend(MMinusRegistry.entries_from_oak_report(obj, report))

print(report.status)
print(route)
```

## OAK-safe

Ce package ne déclare pas une information vraie par beauté, cohérence ou compression. Il sépare :

- fait établi,
- hypothèse fertile,
- preuve,
- source,
- incertitude,
- risque,
- statut OAK,
- action suivante.

La règle fondamentale : **compression ≠ vérité**. Une compression peut être fertile tout en étant fausse ou incomplète.

## Architecture

```text
omega_info2_tristan/
  src/omega_info2/
    models.py
    bayes_tristan.py
    cvcd_compressor.py
    m_minus_registry.py
    source_trust.py
    half_life.py
    oak_gate.py
    router.py
    graph.py
    claim_extractor.py
    cli.py
  schemas/info2_schema.yaml
  examples/
  tests/
  docs/
```

## Pipeline canonique

```text
GO INFO²-GITHUB
1. Construire InfoObject
2. Estimer SourceTrust + Freshness
3. Mettre à jour Bayes-Tristan vectoriel
4. Extraire invariants CVCD + résidus
5. Passer OAKInfoGate
6. Router vers PROTOTYPE / PATENT_HOLD / M_MINUS / CANON_CANDIDATE / ARCHIVE
7. Sauvegarder les erreurs dans MMinusRegistry
8. Produire Info2Graph
```

Cette commande transforme une idée, un PDF, une mesure, une source web, un brevet, un code ou une théorie en objet informationnel traçable, testable, compressible et actionnable.
