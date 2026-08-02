# Ω-SANS-PLAFOND-T∞ R0.4

## Boucle d’auto-amélioration OAK-safe

**Statut :** prototype logiciel hors ligne, déterministe, mesurable et réversible. Il ne constitue ni une autonomie générale, ni une permission de modifier ou publier automatiquement du code.

## 1. But

R0.4 applique Ω-SANS-PLAFOND-T∞ à sa propre politique de contrôle :

```text
INCUMBENT
  → OAKBENCH MULTI-ÉCHELLE
  → M⁻ DES SATURATIONS
  → CANDIDATS DE RECONCEPTION
  → OAKBENCH COMPARATIF
  → REJET DES RÉGRESSIONS
  → M⁺ DU GAIN MESURÉ
  → PLAN DE PROMOTION HUMAIN
  → NOUVEL INCUMBENT APRÈS APPROBATION
  → RÉPÉTITION
```

Le système ne suppose jamais qu’une nouvelle version est meilleure parce qu’elle est plus agressive, plus volumineuse ou plus complexe. Elle doit gagner sa promotion par mesure comparative.

## 2. Distinction fondamentale

L’objectif global reste ouvert :

```text
aucun plafond permanent de candidats, d’itérations ou d’ajouts
```

Une expérience concrète reste bornée par :

- le flux de candidats fourni;
- les scénarios finis choisis;
- les ressources physiques;
- les exigences de qualité et de récupération;
- les permissions;
- les règles de sécurité, de droit, d’IP et des fournisseurs.

R0.4 ne contient aucun `MAX_CANDIDATES` ou `MAX_SELF_IMPROVEMENT_ROUNDS`. Le laboratoire consomme un itérable jusqu’à son épuisement ou jusqu’à un arrêt réel gouverné.

## 3. Objet amélioré

La première version améliore les paramètres mesurables du contrôleur et de l’exécuteur synthétique :

```yaml
stable_growth: croissance après un lot très stable
cautious_growth: croissance près de la pression douce
redesign_factor: amplitude d’une reconception de frontière
pressure_soft: seuil de croissance prudente
pressure_hard: seuil d’échec du lot
quality_floor: qualité minimale acceptée
```

Cette portée limitée est intentionnelle. Elle démontre une boucle récursive falsifiable avant toute tentative de modification structurelle du code.

## 4. Cellule de candidat

Chaque variante est sérialisable et possède une empreinte déterministe :

```yaml
name: mminus-capacity-redesign-plus
stable_growth: 2.0
cautious_growth: 1.25
redesign_factor: 4.0
pressure_soft: 0.75
pressure_hard: 1.0
quality_floor: 0.95
fingerprint: sha256-tronqué
```

Deux variantes sémantiquement identiques ont la même empreinte même si leur nom diffère. Les doublons sont rejetés avant évaluation et inscrits dans M⁻.

## 5. OAKBench multi-échelle

Une variante est évaluée sur plusieurs scénarios de tailles et capacités différentes. Pour chaque scénario, R0.4 conserve :

- statut final;
- travail intégré;
- rejets et doublons;
- nombre d’itérations;
- saturations;
- reconceptions;
- plus grand lot sûr;
- capacité finale observée;
- nombre d’événements M⁻.

La métrique d’efficacité actuelle est :

```text
efficiency = integrated_work /
             (iterations + 8*saturations + 4*redesigns)
```

Cette métrique est une fonction de sélection interne, pas une loi universelle. Son poids doit lui-même devenir un futur objet d’expérience et de falsification.

## 6. Conditions de promotion

Une variante n’est admissible que si :

1. tous les scénarios se terminent;
2. le travail intégré ne diminue pas;
3. les rejets n’augmentent pas;
4. les doublons n’augmentent pas;
5. les itérations n’augmentent pas;
6. les saturations n’augmentent pas;
7. le gain d’efficacité dépasse le seuil expérimental;
8. la promotion reste soumise à approbation humaine.

La meilleure variante admissible est sélectionnée selon :

```text
efficacité maximale
→ saturations minimales
→ itérations minimales
→ plus grand lot sûr
```

## 7. Mémoire récursive

### M⁻

`self_improvement_m_minus.jsonl` contient notamment :

- candidats dupliqués;
- candidats non promus;
- régressions mesurées;
- résultats complets permettant de reproduire le rejet.

Chaque scénario possède également son propre journal M⁻ de saturation.

### M⁺

`m_plus.jsonl` enregistre une amélioration mesurée seulement lorsqu’une variante franchit tous les gates. Le statut reste :

```text
promotion_candidate_requires_human_approval
```

Une seule exécution ne canonise pas le gain. Une reproduction indépendante reste nécessaire.

## 8. Sorties

```text
self-improvement-report.json
promotion-plan.json
candidate-results.jsonl
self_improvement_m_minus.jsonl
m_plus.jsonl
variants/
  baseline-<fingerprint>/
  candidate-<fingerprint>/
```

Le plan de promotion contient explicitement :

```yaml
automatic: false
requires_human_approval: true
source_mutations: 0
remote_mutations: 0
merge: false
```

## 9. CLI

```bash
omega-unbounded self-improve \
  --work-items 60000 \
  --minimum-improvement-ratio 0.02 \
  --output-dir generated/omega_unbounded_self_improvement
```

Flux externe extensible de variantes :

```bash
omega-unbounded self-improve \
  --candidates candidates.jsonl \
  --work-items 60000 \
  --output-dir generated/omega_unbounded_self_improvement
```

Le fichier JSONL est lu en streaming jusqu’à épuisement; le laboratoire ne lui impose pas de nombre maximal permanent.

## 10. Ce que R0.4 améliore réellement

R0.4 peut découvrir qu’une reconception de capacité plus forte réduit simultanément le nombre de saturations et le nombre d’itérations sur les scénarios testés. Il peut alors proposer ce nouveau paramètre comme prochain incumbent.

Il ne prouve pas que le candidat sera meilleur :

- sur tous les matériels;
- sur tout type de charge;
- avec des API réelles;
- sur des dépôts géants;
- face à des coûts, latences ou erreurs non simulés;
- pour une modification structurelle du code.

## 11. Limites et M⁻ initiale

- Le premier benchmark utilise encore un exécuteur synthétique.
- La métrique d’efficacité est conçue manuellement.
- Les scénarios par défaut ne couvrent pas les API GitHub réelles.
- La promotion est configurationnelle; elle ne produit pas encore un patch de code vérifié.
- Un facteur de reconception plus grand pourrait surallouer des ressources dans le monde réel.
- Le journal M⁺ représente une preuve interne, pas une validation indépendante.

## 12. Frontière R0.5

La prochaine couche doit coupler la même boucle à des mesures réelles et réversibles :

1. profiler mémoire, disque et temps du planificateur streaming;
2. générer des candidats de sharding, cache, batch et index SQLite;
3. exécuter des benchmarks différentiels sur plusieurs tailles de corpus;
4. produire des patches dans un arbre temporaire isolé;
5. compiler et tester chaque patch;
6. comparer baseline et patch;
7. ouvrir une PR brouillon seulement après approbation explicite;
8. ne jamais fusionner automatiquement.

## 13. Règle canonique

> Ω-SANS-PLAFOND-T∞ peut s’améliorer lui-même seulement en transformant ses erreurs en candidats falsifiables, en mesurant chaque candidat contre l’incumbent, en rejetant toute régression, en conservant M⁻ et M⁺, et en laissant toute mutation durable sous souveraineté humaine.
