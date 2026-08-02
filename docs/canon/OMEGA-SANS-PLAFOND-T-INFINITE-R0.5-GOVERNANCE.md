# Ω-SANS-PLAFOND-T∞ R0.5

## StopGate, mémoire négative réflexe et gouvernance Pareto

**Statut :** prototype logiciel hors ligne, déterministe, testable et sans autorité distante.

## 1. Problème corrigé

Un système sans plafond arbitraire peut confondre deux choses :

```text
continuer parce que la frontière reste fertile
continuer parce qu’il ne sait pas s’arrêter
```

R0.5 introduit une gouvernance explicite de l’arrêt. Le but n’est plus de maximiser le nombre d’itérations, mais de maximiser le taux d’améliorations vraies par unité de temps, de ressources et de complexité.

## 2. Boucle gouvernée

```text
OBSERVATION
→ INFORMATION MARGINALE
→ VALIDATION
→ RISQUE NOUVEAU?
→ STOPGATE
→ CONTINUE ou STOP
→ M⁻ RÉFLEXE
→ TEST DE NON-RÉCIDIVE
```

Une interruption explicite de Tristan possède la priorité absolue. Une nouvelle découverte critique peut garder l’enquête ouverte, mais une validation répétée sans information nouvelle doit arrêter la boucle.

## 3. StopGate

Le StopGate utilise des observations sérialisables :

```yaml
objective_reached: true
authoritative_validation: true
marginal_information_gain: 0.01
repetition_score: 0.95
validation_fingerprint: authoritative-proof-a
critical_new_risk: false
user_interrupt: false
```

La politique par défaut est :

```yaml
minimum_marginal_information: 0.02
maximum_repetition_score: 0.90
maximum_equivalent_validations: 2
maximum_stagnant_observations: 2
```

Le système s’arrête notamment lorsque :

1. Tristan interrompt l’exécution;
2. l’objectif est atteint;
3. une validation autoritative existe;
4. l’information marginale est faible et la répétition élevée;
5. deux validations équivalentes sont déjà présentes, afin d’empêcher une troisième vérification redondante.

Il continue lorsqu’un risque critique nouveau exige encore une investigation.

## 4. M⁻ réflexe

La mémoire négative devient active. Une erreur ne produit plus uniquement un rapport; elle produit une règle capable de bloquer le comportement fautif.

```yaml
trigger: objective_reached_and_authoritative_validation_obtained
blocked_action: repeat_equivalent_validation
correction:
  - invoke StopGate
  - stop before a third equivalent validation
regression_test:
  - no_third_equivalent_validation
  - user_interrupt_stops_immediately
scope:
  - assistant
  - ci
  - agents
  - self_improvement_lab
```

Les règles sont écrites dans un journal JSONL append-only et peuvent être rechargées lors d’une exécution ultérieure.

## 5. Gouvernance multiobjectif

Un seul score peut être exploité. R0.5 introduit donc des vecteurs d’objectifs :

```yaml
maximize:
  quality: 1.0
  throughput: 10.0
minimize:
  memory: 8.0
```

Un candidat domine un autre seulement s’il n’est pire sur aucun objectif et strictement meilleur sur au moins un objectif. Le front de Pareto conserve les compromis non dominés et retire les candidats clairement inférieurs.

Exemple :

```text
fast   : débit supérieur, mémoire supérieure
lean   : débit inférieur, mémoire inférieure
dominated : débit inférieur et mémoire supérieure
```

Le front conserve `fast` et `lean`, mais rejette `dominated`.

Le front de Pareto n’accorde pas automatiquement une permission de promotion. Il devient une preuve supplémentaire destinée au Judge-of-Judges et à l’approbation humaine.

## 6. Commande reproductible

```bash
omega-unbounded governance-check \
  --output-dir generated/omega_unbounded_governance
```

Sorties :

```text
governance-report.json
m_minus_reflex.jsonl
```

Le contrôle vérifie :

- continuation avant preuve suffisante;
- arrêt après preuve suffisante;
- activation d’une règle M⁻ anti-suritération;
- élimination d’un point dominé;
- conservation de deux compromis Pareto;
- zéro mutation de source;
- zéro mutation distante.

## 7. OAKBench

Les tests couvrent :

1. interruption immédiate;
2. arrêt après validation autoritative à faible information marginale;
3. blocage d’une troisième validation équivalente;
4. maintien de l’enquête face à un risque critique nouveau;
5. persistance et rechargement de M⁻;
6. dominance et front de Pareto.

## 8. Limites

- La notion de validation autoritative dépend encore du contexte externe.
- Les scores d’information et de répétition doivent être calibrés sur des traces réelles.
- Une règle M⁻ peut devenir obsolète et devra ultérieurement posséder un mécanisme de révision contrôlée.
- Le front de Pareto ne résout pas seul les conflits éthiques, légaux ou de sécurité.
- R0.5 n’autorise aucune mutation automatique de code, branche, PR ou dépôt.

## 9. Frontière R0.6

La prochaine couche peut relier ces primitives au laboratoire R0.4 par une intégration séparée et explicitement autorisée :

```text
candidats admissibles
→ vecteurs multiobjectifs
→ front de Pareto
→ juges adversariaux indépendants
→ StopGate après preuve suffisante
→ plan de promotion humain
```

Toute intégration devra préserver :

```yaml
source_mutations: 0
remote_mutations: 0
automatic_merge: false
human_approval_required: true
```

## 10. Règle canonique

> Ω-SANS-PLAFOND-T∞ ne signifie pas continuer sans fin. Il signifie ne pas imposer de plafond arbitraire à la découverte tout en arrêtant immédiatement lorsque la preuve est suffisante, l’information marginale faible, la répétition élevée ou Tristan l’ordonne.
