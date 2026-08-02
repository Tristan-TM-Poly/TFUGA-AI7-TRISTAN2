# Ω-ECC-T — Correction d’erreurs de Tristan

**Identifiant :** `omega-ecc-t`  
**Version :** `R0.2-public`  
**Maturité :** `prototype`  
**Preuve :** `tests déterministes`

## Résumé

Relie codes classiques, syndromes, hypergraphes de parité et mémoire négative dans un laboratoire reproductible.

## Statut épistémique

Un score de syndrome ne remplace ni preuve de correction générale ni modèle réaliste du canal.

Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.

## Domaines

- information
- codes correcteurs
- fiabilité

## Profil OAK provisoire

| Dimension | Signal |
|---|---:|
| verite | 0.56 |
| utilite | 0.84 |
| testabilite | 0.92 |
| simplicite | 0.55 |
| valeur | 0.76 |
| protection | 0.63 |

Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.

## Claims publics

### claim-omega-ecc-t-01 — Portée publique et objet testable

- Type: `scope`
- Statut: `candidate`
- Énoncé: Ω-ECC-T propose un cadre structuré pour relie codes classiques, syndromes, hypergraphes de parité et mémoire négative dans un laboratoire reproductible.
- Limite: La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.
- Prochain test: Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.

### claim-omega-ecc-t-02 — Limite OAK obligatoire

- Type: `limit`
- Statut: `guardrail`
- Énoncé: La promotion de Ω-ECC-T reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.
- Limite: Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.
- Prochain test: Auditer page, dépôt, tests et sources pour détecter une divergence réelle.

### claim-omega-ecc-t-03 — Prochaine falsification ou réduction

- Type: `test-plan`
- Statut: `planned`
- Énoncé: La prochaine progression de Ω-ECC-T doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.
- Limite: Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.
- Prochain test: Comparer Hamming, BCH/LDPC simples et canaux burst avec coût, latence et taux résiduel.

## Relations sortantes

- `crystallized_by` → `omega-tristan-self-os` — Traverse capture, canon, OAK, prototype, IP et valeur.
- `documented_by` → `omega-doc-t` — Claims, versions, limites et résidus restent documentés.
- `mapped_by` → `omega-atlas-t` — Coordonnées, provenance, statut, risques et routes restent navigables.
- `uncertainty_guard` → `omega-unc2-t` — Incertitudes, désaccords et domaines de validité restent explicites.
- `published_through` → `omega-web-tristan-t` — La couche publique expose seulement le résumé validé par les quatre gates.

## Relations entrantes

- `same_family` ← `omega-cvcd-t` — Famille partagée: compute

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

Comparer Hamming, BCH/LDPC simples et canaux burst avec coût, latence et taux résiduel.

## Provenance

- Source: `docs/theory_cards/OMEGA_ECC_T.md`
- Mise à jour: `2026-08-02`

## Gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.
