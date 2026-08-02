# Ω-CHEM-LOG-LIN-T — Cinétique chimique en coordonnées logarithmiques

**Identifiant :** `omega-chem-log-lin-t`  
**Version :** `R0.2-public`  
**Maturité :** `architecture`  
**Preuve :** `cas tests requis`

## Résumé

Transforme les lois multiplicatives et vitesses relatives en représentations log pour analyse et approximation.

## Statut épistémique

Toutes les EDO chimiques ne deviennent pas globalement linéaires et les concentrations doivent rester positives.

Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.

## Domaines

- chimie
- EDO
- mathématiques

## Profil OAK provisoire

| Dimension | Signal |
|---|---:|
| verite | 0.45 |
| utilite | 0.77 |
| testabilite | 0.73 |
| simplicite | 0.50 |
| valeur | 0.71 |
| protection | 0.67 |

Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.

## Claims publics

### claim-omega-chem-log-lin-t-01 — Portée publique et objet testable

- Type: `scope`
- Statut: `candidate`
- Énoncé: Ω-CHEM-LOG-LIN-T propose un cadre structuré pour transforme les lois multiplicatives et vitesses relatives en représentations log pour analyse et approximation.
- Limite: La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.
- Prochain test: Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.

### claim-omega-chem-log-lin-t-02 — Limite OAK obligatoire

- Type: `limit`
- Statut: `guardrail`
- Énoncé: La promotion de Ω-CHEM-LOG-LIN-T reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.
- Limite: Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.
- Prochain test: Auditer page, dépôt, tests et sources pour détecter une divergence réelle.

### claim-omega-chem-log-lin-t-03 — Prochaine falsification ou réduction

- Type: `test-plan`
- Statut: `planned`
- Énoncé: La prochaine progression de Ω-CHEM-LOG-LIN-T doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.
- Limite: Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.
- Prochain test: Comparer réactions d’ordre 1/2, Michaelis–Menten et autocatalyse aux solveurs standards.

## Relations sortantes

- `crystallized_by` → `omega-tristan-self-os` — Traverse capture, canon, OAK, prototype, IP et valeur.
- `documented_by` → `omega-doc-t` — Claims, versions, limites et résidus restent documentés.
- `mapped_by` → `omega-atlas-t` — Coordonnées, provenance, statut, risques et routes restent navigables.
- `uncertainty_guard` → `omega-unc2-t` — Incertitudes, désaccords et domaines de validité restent explicites.
- `published_through` → `omega-web-tristan-t` — La couche publique expose seulement le résumé validé par les quatre gates.
- `shares_domain` → `omega-transform-t` — Domaine partagé: mathématiques
- `same_family` → `omega-oem-mtd-t` — Famille partagée: science
- `shares_domain` → `omega-lin-t` — Domaine partagé: mathématiques
- `same_family` → `omega-neg-t` — Famille partagée: science
- `shares_domain` → `omega-zeta-mandel-t` — Domaine partagé: mathématiques
- `same_family` → `omega-natsci-t` — Famille partagée: science
- `shares_domain` → `omega-fpg-t` — Domaine partagé: mathématiques
- `shares_domain` → `omega-prime-object-t` — Domaine partagé: mathématiques
- `shares_domain` → `omega-fact-infinity-t` — Domaine partagé: mathématiques
- `same_family` → `omega-generator-discovery-stack` — Famille partagée: science

## Relations entrantes


## Risques

- surpromesse
- preuve insuffisante
- artefact numérique
- généralisation abusive

## Artefacts attendus

- fiche publique
- rapport OAK
- prochaine expérience
- spécification
- schéma
- protocole de test

## Prochaine action

Comparer réactions d’ordre 1/2, Michaelis–Menten et autocatalyse aux solveurs standards.

## Provenance

- Source: `docs/theory_cards/OMEGA_CHEM_LOG_LIN_T.md`
- Mise à jour: `2026-08-02`

## Gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.
