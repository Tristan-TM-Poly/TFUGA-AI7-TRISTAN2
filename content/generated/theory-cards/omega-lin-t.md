# Ω-LIN-T — Linéarisation multi-échelle

**Identifiant :** `omega-lin-t`  
**Version :** `R0.2-public`  
**Maturité :** `architecture`  
**Preuve :** `prototype ciblé`

## Résumé

Traite la linéarisation comme atlas de modèles locaux avec domaines de validité et résidus non linéaires conservés.

## Statut épistémique

Une stabilité locale ou un bon ajustement local ne prouve pas un comportement global.

Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.

## Domaines

- mathématiques
- contrôle
- modélisation

## Profil OAK provisoire

| Dimension | Signal |
|---|---:|
| verite | 0.47 |
| utilite | 0.80 |
| testabilite | 0.75 |
| simplicite | 0.46 |
| valeur | 0.74 |
| protection | 0.66 |

Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.

## Claims publics

### claim-omega-lin-t-01 — Portée publique et objet testable

- Type: `scope`
- Statut: `candidate`
- Énoncé: Ω-LIN-T propose un cadre structuré pour traite la linéarisation comme atlas de modèles locaux avec domaines de validité et résidus non linéaires conservés.
- Limite: La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.
- Prochain test: Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.

### claim-omega-lin-t-02 — Limite OAK obligatoire

- Type: `limit`
- Statut: `guardrail`
- Énoncé: La promotion de Ω-LIN-T reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.
- Limite: Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.
- Prochain test: Auditer page, dépôt, tests et sources pour détecter une divergence réelle.

### claim-omega-lin-t-03 — Prochaine falsification ou réduction

- Type: `test-plan`
- Statut: `planned`
- Énoncé: La prochaine progression de Ω-LIN-T doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.
- Limite: Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.
- Prochain test: Créer un atlas Jacobien/Koopman et mesurer l’erreur hors domaine sur systèmes non linéaires.

## Relations sortantes

- `crystallized_by` → `omega-tristan-self-os` — Traverse capture, canon, OAK, prototype, IP et valeur.
- `documented_by` → `omega-doc-t` — Claims, versions, limites et résidus restent documentés.
- `mapped_by` → `omega-atlas-t` — Coordonnées, provenance, statut, risques et routes restent navigables.
- `uncertainty_guard` → `omega-unc2-t` — Incertitudes, désaccords et domaines de validité restent explicites.
- `published_through` → `omega-web-tristan-t` — La couche publique expose seulement le résumé validé par les quatre gates.
- `shares_domain` → `omega-transform-t` — Domaine partagé: mathématiques
- `shares_domain` → `omega-neuro-t` — Domaine partagé: modélisation
- `same_family` → `omega-oem-mtd-t` — Famille partagée: science
- `same_family` → `omega-neg-t` — Famille partagée: science
- `shares_domain` → `omega-zeta-mandel-t` — Domaine partagé: mathématiques
- `shares_domain` → `omega-natsci-t` — Domaine partagé: modélisation
- `shares_domain` → `omega-prime-object-t` — Domaine partagé: mathématiques

## Relations entrantes

- `shares_domain` ← `omega-bat-t` — Domaine partagé: contrôle
- `shares_domain` ← `omega-chem-log-lin-t` — Domaine partagé: mathématiques
- `shares_domain` ← `omega-energy-t` — Domaine partagé: contrôle

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

Créer un atlas Jacobien/Koopman et mesurer l’erreur hors domaine sur systèmes non linéaires.

## Provenance

- Source: `docs/theory_cards/OMEGA_LIN_T.md`
- Mise à jour: `2026-08-02`

## Gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.
