# Ω-REVOLUTION-DIVERSIFICATION-T∞ R0.1

## Diversification vérifiable post-8M

**Statut :** architecture et prototype logiciel OAK-safe.

Cette version convertit l'expansion conceptuelle en trois démonstrateurs exécutables :

1. **M⁻ Ablation** — mesurer si une mémoire négative opérationnelle réduit les erreurs répétées;
2. **GitHub Truth Audit** — comparer documentation, API, tests, versions, chemins et benchmarks;
3. **Raman Discovery Loop** — comparer plusieurs mécanismes synthétiques, une baseline et une expérience discriminante.

La version ajoute aussi une `DiscoveryCell`, un portefeuille d'hypothèses, un conducteur de qualité et un registre canonique de **64 modules** répartis en huit groupes.

---

## 1. Pourquoi cette branche existe

Les frontiers 1M, 2M, 4M et 8M ont validé une capacité de workflow :

- génération déterministe;
- interruption forcée;
- reprise exacte;
- indexation;
- absence de doublons;
- absence de parents orphelins;
- décisions adaptatives.

Cette capacité ne démontre pas encore une valeur scientifique ou économique. R0.1 change donc l'objectif :

```text
volume validé
→ diversité utile
→ comparaison
→ falsification
→ mémoire
→ utilisateur
→ valeur externe
```

La règle centrale devient :

> Aucun gain de volume ne constitue un progrès complet sans gain parallèle de preuve, de diversité causale, de validation externe et de conversion en actif.

---

## 2. DiscoveryCell

La `DiscoveryCell` est une unité commune de recherche, d'ingénierie, de mémoire et de produit.

Elle contient : problème, utilisateur, douleur observable, baseline, hypothèses falsifiables, preuves typées ou contradictoires, quantités et unités, code, tests, mémoire M⁻, actions, valeurs scientifique/technique/produit, statut OAK et état IP.

Une cellule démontrée ne peut pas être valide sans résultat ou mesure, baseline, conditions d'échec et références cohérentes. Le schéma machine strict est `schemas/discovery-cell-r0-1.schema.json`.

---

## 3. Portefeuille d'hypothèses

Chaque hypothèse reçoit un score de routage :

```text
priorité ≈
valeur × gain d'information × falsifiabilité × réutilisabilité
──────────────────────────────────────────────────────────────
coût × temps × incertitude opérationnelle × dépendances
```

Ce score n'est ni une probabilité, ni une preuve, ni une décision autonome de financement. Il sert à prioriser des tests comparables avec minimum par hypothèse, part maximale, normalisation déterministe et protection contre la monoculture.

---

## 4. QualityConductor

Le conducteur observe objets générés et uniques, claims formalisés, preuves, falsification, validations externes, doublons, orphelins, preuves circulaires et efficacité M⁻.

- `EXPAND` : qualité et validation externe passent;
- `RESHARD` : le bruit croît trop vite;
- `HOLD` : dette de preuve, falsification ou validation externe;
- `REDESIGN` : intégrité ou mémoire négative défaillante;
- `STOP` : enveloppe de ressources ou gate humain.

Le système peut donc refuser l'expansion même lorsque le débit augmente.

---

## 5. M⁻ Ablation

Le module compare un contrôleur sans mémoire négative à un contrôleur avec règles structurées : trigger, cause, inférence interdite, remplacement sûr, test de prévention, domaine, sévérité et sources.

Les métriques incluent coût, erreurs, récurrence, prévention, faux blocages, précision et rappel. Le fixture couvre baseline absente, unités incohérentes, mutation directe, documentation obsolète, projection commerciale présentée comme fait et contrôles sûrs.

**Limite :** une règle M⁻ trop large peut bloquer un cas sûr; le système mesure donc aussi les faux blocages.

---

## 6. GitHub Truth Audit

Le Truth Audit compare claims documentaires, symboles publics/testés/dépréciés, chemins, versions, dépendances et benchmarks. Il détecte versions divergentes, symboles ou chemins absents, API sans tests, claims de tests non supportés, dépendances divergentes et complexité empirique incompatible avec la documentation.

Une divergence est une candidate de revue, pas une preuve d'intention, de fraude ou de faute juridique.

---

## 7. Raman Discovery Loop

Le démonstrateur synthétique compare trois mécanismes : déplacement seul, déplacement + élargissement, et déplacement + élargissement + dérive de baseline.

```text
référence → entraînement → fit → holdout → baseline
→ pénalité de complexité → classement
→ expérience discriminante → transition OAK → M⁻ si échec
```

Le fixture ne prétend pas identifier une molécule, remplacer une calibration, prouver une causalité réelle ou imposer les Lorentziennes à tous les spectres.

---

## 8. Registre 64 modules

Huit groupes de huit modules : connaissance, expériences, générateurs, logiciel, mémoire, valeur, IP/sécurité et gouvernance. Chaque entrée possède rôle, preuve requise, premier gate et risque. Sa présence dans le catalogue ne signifie pas qu'elle est implémentée ou validée.

---

## 9. Adaptateurs

Les adaptateurs duck-typed relient les `KnowledgeCell` existantes aux `DiscoveryCell` et convertissent les événements `MMinusRule`, `RefutationEvent` et `FailureEvent` en mémoire négative structurée. Une cellule importée reste à auditer avant promotion.

---

## 10. CLI

```bash
python -m omega_revolution_diversification_t registry
python -m omega_revolution_diversification_t mminus-ablation
python -m omega_revolution_diversification_t truth-audit
python -m omega_revolution_diversification_t raman-loop
python -m omega_revolution_diversification_t quality-demo
python -m omega_revolution_diversification_t compile-demo \
  --output-dir generated/omega_revolution_diversification_r0_1
```

Le bundle produit manifest, métriques, registre, cellules JSON/JSONL, audits, ablation, Raman, décision qualité et rapport Markdown.

---

## 11. Gates CI

Le workflow dédié vérifie compilation, 33 tests, schéma JSON, registre 8×8, toutes les commandes CLI, bundle complet et trois preuves : M⁻ réduit le coût de fixture, le modèle Raman complet bat la baseline synthétique et le Truth Audit détecte plusieurs divergences connues.

---

## 12. Politique OAK

Trois fronts profonds maximum. `DEMONSTRATED` exige résultat, baseline et condition d'échec. `REPLICATED` exige une réplication indépendante. `CANONICAL` exige scope, contre-exemples et revue humaine. Publication, déploiement, finance, IP, expériences physiques et données personnelles exigent une approbation humaine. Il n'existe aucun plafond total permanent, mais toute exécution reste finie et gouvernée.

---

## 13. Mémoire négative initiale

- Un grand volume de fixtures ne prouve pas une valeur scientifique.
- Un score non calibré ne doit pas contrôler seul les ressources.
- Un audit interne ne mesure pas la précision externe.
- Une réussite Raman synthétique ne prouve pas une meilleure déconvolution instrumentale.
- Une règle M⁻ trop large peut produire un faux blocage.

---

## 14. Prochaines preuves externes

1. Rejouer des défauts réels pour mesurer récurrence, faux blocages, coût et temps évités.
2. Auditer des dépôts avec labels humains pour mesurer précision, rappel et réduction du temps de revue.
3. Utiliser un dataset Raman public avec calibration, holdout, baselines SciPy, incertitudes et réplication.

---

## 15. Critère de succès

R0.1 est réussi lorsque les trois démonstrateurs sont déterministes, les cellules strictement validées, les frontières explicites, la CI bloquante et le bundle reproductible. Le statut suivant exige des données et utilisateurs externes, pas seulement davantage de lignes.
