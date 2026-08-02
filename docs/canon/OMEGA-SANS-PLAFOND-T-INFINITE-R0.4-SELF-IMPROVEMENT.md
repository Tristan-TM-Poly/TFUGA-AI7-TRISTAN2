# Ω-SANS-PLAFOND-T∞ R0.4

## Boucle d’auto-amélioration récursive OAK-safe

**Statut :** prototype logiciel hors ligne, déterministe, mesurable et réversible. R0.4 améliore une politique de contrôle; il ne reçoit aucune autonomie générale ni permission de modifier, publier ou fusionner du code.

## 1. Boucle canonique

```text
INCUMBENT
  → OAKBENCH MULTI-ÉCHELLE
  → M⁻ DES SATURATIONS ET FAUX GAINS
  → CANDIDATS DE RECONCEPTION
  → OAKBENCH COMPARATIF
  → JUGE ANTI-RÉGRESSION ET ANTI-REWARD-HACKING
  → M⁺ DU GAIN MESURÉ
  → PLAN DE PROMOTION HUMAIN
  → NOUVEL INCUMBENT APRÈS APPROBATION
  → RÉPÉTITION
```

Le système ne suppose jamais qu’une version plus agressive, volumineuse ou complexe est meilleure. Elle doit gagner sa promotion par mesure comparative, sans exploiter une faiblesse de la métrique.

## 2. Objectif sans plafond, exécutions gouvernées

R0.4 ne contient aucun `MAX_CANDIDATES` ni `MAX_SELF_IMPROVEMENT_ROUNDS`. Il consomme un flux de variantes jusqu’à son épuisement ou jusqu’à un arrêt réel gouverné.

Chaque expérience demeure bornée par :

- les scénarios finis choisis;
- les ressources physiques;
- la qualité et la récupérabilité;
- les permissions et coûts;
- les contraintes de sécurité, de droit, d’IP et des fournisseurs.

## 3. Objet actuellement améliorable

La première couche compare des variantes sérialisables de la politique :

```yaml
stable_growth: croissance après un lot stable
cautious_growth: croissance près de la pression douce
redesign_factor: amplitude d’une reconception de frontière
pressure_soft: seuil de croissance prudente
pressure_hard: seuil d’échec du lot
quality_floor: qualité minimale acceptée
fingerprint: empreinte déterministe de la configuration
```

Deux variantes ayant la même configuration partagent la même empreinte même si leur nom diffère. Le doublon est rejeté avant calcul et conservé dans M⁻.

## 4. OAKBench multi-échelle

Les variantes sont comparées sur trois échelles finies et reproductibles. Chaque résultat conserve :

- travail intégré, rejets et doublons;
- itérations, saturations et reconceptions;
- plus grand lot démontré sûr;
- capacité finale allouée;
- événements M⁻;
- statut d’achèvement.

## 5. Juge de ressources

Le premier cycle avait utilisé :

```text
efficiency_raw = integrated_work /
                 (iterations + 8*saturations + 4*redesigns)
```

Cette fonction contenait une faille : une variante pouvait augmenter excessivement la capacité allouée, réduire ses saturations et paraître meilleure sans payer le coût de la surallocation.

R0.4 a détecté ce **reward hacking** pendant son propre cycle. Le juge corrigé utilise :

```text
overshoot = Σ max(0, final_capacity / largest_safe_batch - 1)

efficiency_oak = integrated_work /
                 (iterations
                  + 8*saturations
                  + 4*redesigns
                  + 10*overshoot)
```

Un candidat est aussi rejeté lorsque son overshoot total dépasse le multiplicateur OAK permis relativement à l’incumbent.

## 6. Résultat reproductible du 2 août 2026

### Incumbent R0.3

```yaml
redesign_factor: 2.0
integrated_work: 60000
iterations: 60
saturations: 18
redesigns: 18
efficiency_oak: 209.13358941527954
```

### Candidat promu conditionnellement

```yaml
name: mminus-capacity-redesign
fingerprint: 413ca87f21b78239
redesign_factor: 3.0
integrated_work: 60000
iterations: 50
saturations: 12
redesigns: 12
efficiency_oak: 279.55736750145604
measured_improvement_ratio: 0.33674063684879907
```

Le candidat ×3 conserve tout le travail, réduit les itérations de 60 à 50, réduit les saturations de 18 à 12 et améliore le score corrigé de **33,67 %** sur ces scénarios synthétiques.

### Faux gagnant converti en M⁻

```yaml
name: mminus-capacity-redesign-plus
redesign_factor: 4.0
raw_apparent_improvement: environ 55 pour cent
resource_aware_efficiency: 226.66344047895834
oak_status: rejected
reason: capacity overshoot exceeded the permitted multiplier
```

Le facteur ×4 avait gagné avec la métrique naïve, mais seulement au prix d’une forte surallocation. Cette découverte devient une mémoire négative permanente : **optimiser la métrique n’est pas nécessairement améliorer le système**.

## 7. Conditions de promotion

Une variante n’est admissible que si :

1. tous les scénarios se terminent;
2. le travail intégré ne diminue pas;
3. les rejets et doublons n’augmentent pas;
4. les itérations et saturations n’augmentent pas;
5. le score corrigé dépasse le seuil expérimental;
6. la surallocation reste dans le multiplicateur OAK;
7. le plan conserve zéro mutation automatique;
8. la promotion reste soumise à approbation humaine;
9. une reproduction indépendante précède la canonisation définitive.

## 8. Mémoire récursive

### M⁻

`self_improvement_m_minus.jsonl` conserve :

- variantes dupliquées;
- régressions;
- variantes non promues;
- surallocation et reward hacking;
- résultats complets permettant de reproduire le rejet.

### M⁺

`m_plus.jsonl` conserve uniquement les gains ayant franchi tous les gates. Leur statut reste :

```text
promotion_candidate_requires_human_approval
```

## 9. Sorties

```text
self-improvement-report.json
promotion-plan.json
candidate-results.jsonl
self_improvement_m_minus.jsonl
m_plus.jsonl
variants/
```

Le plan contient obligatoirement :

```yaml
automatic: false
requires_human_approval: true
source_mutations: 0
remote_mutations: 0
merge: false
```

## 10. CLI

```bash
omega-unbounded self-improve \
  --work-items 60000 \
  --minimum-improvement-ratio 0.02 \
  --overshoot-penalty-weight 10 \
  --maximum-overshoot-multiplier 2 \
  --output-dir generated/omega_unbounded_self_improvement
```

Un flux JSONL externe de variantes peut remplacer le voisinage initial. Il est lu en streaming sans plafond permanent de nombre de candidats.

## 11. Limites actuelles

- Le benchmark est encore synthétique.
- Les poids du juge sont des hypothèses testables, non des lois universelles.
- Le gain ×3 n’est pas encore démontré sur les API GitHub réelles.
- La promotion est configurationnelle; aucun patch source n’est auto-appliqué.
- Une reproduction indépendante reste requise.

## 12. Frontière R0.5

R0.5 doit appliquer la boucle à des mesures réelles et réversibles : mémoire, disque, temps, SQLite, sharding, cache et reprise après interruption. Les patches candidats devront être produits dans des arbres temporaires isolés, compilés, testés et comparés, puis seulement proposés dans une PR brouillon explicitement autorisée. Aucune auto-fusion.

## 13. Règle canonique

> Ω-SANS-PLAFOND-T∞ peut s’améliorer lui-même seulement en transformant ses erreurs et faux gains en candidats falsifiables, en mesurant chaque candidat contre l’incumbent avec un juge résistant au reward hacking, en rejetant toute régression ou surallocation, en conservant M⁻ et M⁺, et en laissant toute mutation durable sous souveraineté humaine.
