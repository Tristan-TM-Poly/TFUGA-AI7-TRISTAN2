# Ω-MAIL-T — Laboratoire de courriels intercompagnies

**Identifiant :** `omega-mail-t`  
**Version :** `R0.2-public`  
**Maturité :** `architecture`  
**Preuve :** `MVP fermé`

## Résumé

Génère et teste des fils de courriels synthétiques entre compagnies et agents dans un transport fermé.

## Statut épistémique

Aucun envoi externe, massif ou commercial sans consentement, conformité, throttling et approbation.

Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.

## Domaines

- courriel
- simulation
- agents IA

## Profil OAK provisoire

| Dimension | Signal |
|---|---:|
| verite | 0.45 |
| utilite | 0.85 |
| testabilite | 0.83 |
| simplicite | 0.45 |
| valeur | 0.75 |
| protection | 0.59 |

Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.

## Claims publics

### claim-omega-mail-t-01 — Portée publique et objet testable

- Type: `scope`
- Statut: `candidate`
- Énoncé: Ω-MAIL-T propose un cadre structuré pour génère et teste des fils de courriels synthétiques entre compagnies et agents dans un transport fermé.
- Limite: La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.
- Prochain test: Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.

### claim-omega-mail-t-02 — Limite OAK obligatoire

- Type: `limit`
- Statut: `guardrail`
- Énoncé: La promotion de Ω-MAIL-T reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.
- Limite: Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.
- Prochain test: Auditer page, dépôt, tests et sources pour détecter une divergence réelle.

### claim-omega-mail-t-03 — Prochaine falsification ou réduction

- Type: `test-plan`
- Statut: `planned`
- Énoncé: La prochaine progression de Ω-MAIL-T doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.
- Limite: Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.
- Prochain test: Implémenter boîtes en mémoire, scénarios YAML, assertions, erreurs simulées et rapports de couverture.

## Relations sortantes

- `crystallized_by` → `omega-tristan-self-os` — Traverse capture, canon, OAK, prototype, IP et valeur.
- `documented_by` → `omega-doc-t` — Claims, versions, limites et résidus restent documentés.
- `mapped_by` → `omega-atlas-t` — Coordonnées, provenance, statut, risques et routes restent navigables.
- `uncertainty_guard` → `omega-unc2-t` — Incertitudes, désaccords et domaines de validité restent explicites.
- `published_through` → `omega-web-tristan-t` — La couche publique expose seulement le résumé validé par les quatre gates.

## Relations entrantes

- `shares_domain` ← `omega-corp-jarvis-t` — Domaine partagé: agents IA
- `shares_domain` ← `omega-energy-t` — Domaine partagé: simulation
- `shares_domain` ← `omega-game-t` — Domaine partagé: simulation

## Risques

- surpromesse
- preuve insuffisante

## Artefacts attendus

- fiche publique
- rapport OAK
- prochaine expérience
- spécification
- schéma
- protocole de test

## Prochaine action

Implémenter boîtes en mémoire, scénarios YAML, assertions, erreurs simulées et rapports de couverture.

## Provenance

- Source: `docs/theory_cards/OMEGA_MAIL_T.md`
- Mise à jour: `2026-08-02`

## Gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.
