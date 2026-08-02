# Ω-TRANSFORM-T — Transformées multi-échelles de Tristan

**Identifiant :** `omega-transform-t`  
**Version :** `R0.2-public`  
**Maturité :** `prototype`  
**Preuve :** `test partiel`

## Résumé

Relie FWT, extensions fractales, tensorisation et analyse multi-échelle pour compression, reconstruction et détection.

## Statut épistémique

La pondération fractale naïve n’a pas battu la FWT standard sur le premier benchmark de reconstruction.

Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.

## Domaines

- mathématiques
- signal
- IA

## Profil OAK provisoire

| Dimension | Signal |
|---|---:|
| verite | 0.61 |
| utilite | 0.85 |
| testabilite | 0.84 |
| simplicite | 0.48 |
| valeur | 0.75 |
| protection | 0.63 |

Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.

## Claims publics

### claim-omega-transform-t-01 — Portée publique et objet testable

- Type: `scope`
- Statut: `candidate`
- Énoncé: Ω-TRANSFORM-T propose un cadre structuré pour relie FWT, extensions fractales, tensorisation et analyse multi-échelle pour compression, reconstruction et détection.
- Limite: La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.
- Prochain test: Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.

### claim-omega-transform-t-02 — Limite OAK obligatoire

- Type: `limit`
- Statut: `guardrail`
- Énoncé: La promotion de Ω-TRANSFORM-T reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.
- Limite: Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.
- Prochain test: Auditer page, dépôt, tests et sources pour détecter une divergence réelle.

### claim-omega-transform-t-03 — Prochaine falsification ou réduction

- Type: `test-plan`
- Statut: `planned`
- Énoncé: La prochaine progression de Ω-TRANSFORM-T doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.
- Limite: Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.
- Prochain test: Comparer sur anomalies, débruitage, classification et coût de calcul.

### claim-omega-transform-t-negative-01 — M⁻ — la pondération fractale naïve ne gagne pas au premier benchmark

- Type: `negative-memory`
- Statut: `negative_result`
- Énoncé: Sur le premier signal synthétique documenté, une FWT standard a obtenu une meilleure erreur de reconstruction que la FFWT heuristique à fraction conservée comparable.
- Limite: Résultat local; aucune conclusion générale sur toutes les FFWT ou toutes les tâches.
- Prochain test: Répéter sur plusieurs classes de signaux avec intervalles, coût et baselines.

## Relations sortantes

- `crystallized_by` → `omega-tristan-self-os` — Traverse capture, canon, OAK, prototype, IP et valeur.
- `documented_by` → `omega-doc-t` — Claims, versions, limites et résidus restent documentés.
- `mapped_by` → `omega-atlas-t` — Coordonnées, provenance, statut, risques et routes restent navigables.
- `uncertainty_guard` → `omega-unc2-t` — Incertitudes, désaccords et domaines de validité restent explicites.
- `published_through` → `omega-web-tristan-t` — La couche publique expose seulement le résumé validé par les quatre gates.
- `shares_domain` → `omega-unc2-t` — Domaine partagé: IA
- `shares_domain` → `omega-zeta-mandel-t` — Domaine partagé: mathématiques

## Relations entrantes

- `shares_domain` ← `omega-cvcd-t` — Domaine partagé: IA
- `same_family` ← `omega-oem-mtd-t` — Famille partagée: science
- `shares_domain` ← `omega-lin-t` — Domaine partagé: mathématiques
- `shares_domain` ← `omega-chem-log-lin-t` — Domaine partagé: mathématiques
- `shares_domain` ← `omega-game-t` — Domaine partagé: IA
- `same_family` ← `omega-neg-t` — Famille partagée: science

## Risques

- surpromesse
- preuve insuffisante
- artefact numérique
- généralisation abusive

## Artefacts attendus

- fiche publique
- rapport OAK
- prochaine expérience
- code exécutable
- tests
- benchmark

## Prochaine action

Comparer sur anomalies, débruitage, classification et coût de calcul.

## Provenance

- Source: `docs/theory_cards/OMEGA_TRANSFORM_T.md`
- Mise à jour: `2026-08-02`

## Gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.
