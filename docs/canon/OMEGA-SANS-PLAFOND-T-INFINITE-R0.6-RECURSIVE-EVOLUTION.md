# Ω-SANS-PLAFOND-T∞ R0.6

## Évolution récursive preuve-portante, adversariale et réversible

**Statut OAK :** prototype logiciel hors ligne. Il évalue, compare et prépare des preuves. Il ne déploie, ne fusionne et ne modifie automatiquement aucune source.

## 1. Problème traité

R0.4 a démontré qu’une métrique naïve pouvait sélectionner un faux gagnant par surallocation. R0.5 a ajouté StopGate, M⁻ réflexe et gouvernance Pareto. R0.6 ferme la boucle suivante :

```text
CANDIDAT
→ OAKBENCH ADVERSARIAL
→ GATES DURS
→ FRONT PARETO
→ PREUVE TRANSPORTABLE
→ CANARI 1%-5%-20%-50%-100%
→ PROMOTION CANDIDATE OU ROLLBACK
→ M⁺ / M⁻
→ APPROBATION HUMAINE
```

## 2. Candidat mesurable

Chaque candidat possède un profil explicite :

```yaml
throughput: travail utile par unité de temps
memory_bytes: mémoire observée
latency_ms: latence
quality: qualité mesurée
recovery_rate: capacité de récupération
complexity: coût structurel
overshoot: surallocation
source_mutations: compteur de mutations locales
remote_mutations: compteur de mutations distantes
fingerprint: empreinte déterministe
```

Un changement de nom ne change pas son empreinte lorsque les paramètres restent identiques.

## 3. OAKBench adversarial

Les scénarios par défaut incluent :

- nominal;
- tempête de doublons;
- entrées invalides;
- corruption de checkpoint;
- latence et erreurs d’API.

Pour chaque scénario, R0.6 mesure :

- débit utile;
- mémoire;
- latence;
- qualité;
- récupération;
- violations des gates.

Les mutations source ou distantes constituent des échecs durs. Un candidat rapide ne peut donc jamais compenser une violation d’autorité par un meilleur score.

## 4. Sélection multiobjectif

Les objectifs maximisés sont :

```text
throughput, qualité, récupération
```

Les objectifs minimisés sont :

```text
mémoire, latence, complexité, overshoot
```

R0.6 conserve tous les candidats non dominés. Aucun score scalaire ne possède l’autorité finale.

Le self-check déterministe conserve deux compromis :

```yaml
fast: débit et latence
lean: mémoire, complexité et overshoot
```

Un candidat clairement inférieur est retiré du front. Un candidat fragile est rejeté par les gates adversariales.

## 5. Proof-Carrying Improvement

Chaque candidat admissible transporte un bundle :

```text
candidate.json
adversarial-scenarios.json
oakbench-result.json
canary-report.json
rollback-plan.json
authority.json
manifest.json
```

Le manifeste contient le SHA-256 de chaque fichier et un identifiant de bundle dérivé de son contenu. Une preuve peut donc être copiée, auditée et vérifiée indépendamment.

## 6. Promotion canari simulée

Les étapes sont :

```text
1% → 5% → 20% → 50% → 100%
```

À chaque étape, le moteur vérifie :

- baisse maximale de qualité;
- ratio maximal de latence;
- ratio maximal de mémoire;
- récupération minimale.

Une régression produit immédiatement :

```yaml
action: ROLLBACK
automatic_execution: false
requires_human_approval: true
```

R0.6 démontre les deux chemins :

- un canari sain atteint `promotion_candidate`;
- une baisse de qualité injectée à 20 % déclenche `rolled_back`.

## 7. Mémoire

### M⁻

`m_minus.jsonl` conserve :

- rejet adversarial;
- échec de récupération;
- mutation interdite;
- régression canari;
- plan de rollback associé.

### M⁺

`m_plus.jsonl` conserve un candidat ayant franchi le canari, avec le statut :

```text
promotion_candidate_requires_human_approval
```

Cette inscription n’est pas une canonisation.

## 8. Commande

```bash
omega-unbounded evolution-check \
  --output-dir generated/omega_unbounded_evolution
```

Sorties principales :

```text
evolution-report.json
m_minus.jsonl
m_plus.jsonl
proof-bundles/<fingerprint>/manifest.json
```

## 9. Invariants d’autorité

```yaml
source_mutations: 0
remote_mutations: 0
automatic_pull_request: false
automatic_merge: false
automatic_promotion: false
human_approval_required: true
scalar_score_has_final_authority: false
```

## 10. Limites

- Les scénarios sont synthétiques et déterministes.
- Le canari est une simulation de décision, pas un déploiement réel.
- Les coûts énergétiques et financiers réels ne sont pas encore mesurés.
- Les bundles prouvent l’intégrité des artefacts, pas la vérité universelle de leurs hypothèses.
- Une reproduction indépendante reste nécessaire avant promotion durable.

## 11. Frontière R0.7

R0.7 devra introduire :

1. scénarios aveugles séparés des scénarios de génération;
2. fault injection sur disque, SQLite, réseau et checkpoints;
3. profils réels de temps, mémoire et descripteurs de fichiers;
4. génération de patch dans un arbre éphémère;
5. compilation, tests, fuzzing et analyse statique du patch;
6. comparaison avant/après sur plusieurs environnements;
7. canari réel seulement après autorisation explicite;
8. rollback vérifié et reproductible.

## 12. Règle canonique

> Une amélioration de Tristan ne devient promotable que si elle porte ses preuves, survit à des scénarios adversariaux, demeure non dominée sur les objectifs pertinents, démontre son rollback et conserve zéro autorité durable sans approbation humaine.
