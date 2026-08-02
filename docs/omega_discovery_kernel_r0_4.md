# Ω-DISCOVERY-KERNEL-T∞ R0.4

## Frontier Conductor adaptatif, multi-époques et sans plafond permanent

**Statut :** infrastructure logicielle OAK-safe de planification, observation et décision. Les événements manipulés sont des événements de workflow déterministes. Leur nombre ne constitue ni une preuve scientifique, ni une mesure de vérité, ni une certification de sécurité, ni une conclusion IP ou commerciale.

## 1. Passage de R0.3 à R0.4

R0.3 a démontré un frontier réel de **1 000 000 événements**, interrompu après 524 288 événements puis repris exactement jusqu’à 1 000 000. Cette preuve est conservée.

R0.4 retire cependant une ambiguïté : un million est une frontière expérimentale atteinte, pas l’architecture finale. Le nouveau conducteur remplace les cibles totales codées par une boucle :

```text
ressources finies observables
→ plan géométrique de stages
→ partitions alignées sur la boucle Ω8
→ interruption forcée + reprise
→ télémétrie réelle
→ OAKGate
→ EXPAND | RESHARD | HOLD | REDESIGN | STOP
→ M⁻
→ nouvelle enveloppe ou nouvelle architecture
```

Le système ne contient aucun champ `max_total_events`.

## 2. Ressources qui gouvernent une exécution

Chaque exécution reste physiquement finie. Elle est définie par :

- temps mural disponible;
- octets réellement inscriptibles;
- réserve de rollback;
- mémoire résidente admissible;
- débit minimal;
- taux d’erreur maximal;
- latence maximale d’un batch;
- estimation mesurée des octets par événement;
- estimation mesurée du débit;
- granularité de partition et parallélisme.

Ce sont des **budgets d’exécution**, pas des plafonds permanents du système.

## 3. Échelle géométrique

Le planificateur commence par une frontière initiale, actuellement un million d’événements par défaut, puis propose :

```text
1 M → 2 M → 4 M → 8 M → 16 M → 32 M → ...
```

Chaque stage n’est inclus que si son temps et son stockage projetés tiennent dans l’enveloppe avec la réserve de rollback. Une nouvelle machine, un meilleur format ou un débit amélioré produit automatiquement un plan plus profond sans modifier une constante totale.

Tous les nombres d’événements et toutes les partitions sont alignés sur la boucle fermée :

```text
ObservationEvent
→ ClaimEvent
→ GeneratorCandidate
→ ExperimentSpec
→ ResultPacket
→ OAKTransition
→ MMinusRule
→ ActionProposal
```

Ainsi :

```text
événements = 8 × sujets complets
```

## 4. Décisions du conducteur

### EXPAND

Les contrôles d’intégrité, de qualité, de ressources, de reprise, de mémoire, de latence et de débit passent. Le conducteur propose le prochain stage géométrique.

### RESHARD

L’intégrité passe, mais la mémoire ou la latence de batch sature. Le prochain stage est conservé, tandis que la taille de partition recommandée est divisée pour réduire les pics et augmenter l’indépendance.

### HOLD

La reprise forcée n’a pas été démontrée ou le débit est insuffisant. Le même ordre de grandeur doit être répété après calibration.

### REDESIGN

Un seul des événements suivants bloque toute expansion :

- ID dupliqué;
- parent orphelin;
- sujet incomplet;
- écart entre événements attendus et acceptés;
- taux d’erreur supérieur au contrat.

### STOP

Le prochain stage dépasse l’enveloppe finie actuelle. `STOP` ne signifie pas que le système a atteint sa limite permanente. Il signifie : checkpoint, conservation des preuves, création d’une mémoire M⁻ et demande d’une nouvelle enveloppe ou d’un redesign.

## 5. Mémoire négative automatique

Chaque saturation produit un objet M⁻ contenant :

- type de saturation;
- valeur observée;
- seuil déclaré;
- contexte et SHA du ledger;
- inférence interdite;
- règle réutilisable;
- action de redesign.

Exemples :

> Ne jamais déduire la reprise exacte d’une exécution ininterrompue.

> Ne jamais déduire des boucles complètes du seul nombre brut d’événements.

> Ne jamais masquer la saturation de latence ou de mémoire derrière le débit moyen.

> Ne jamais augmenter l’échelle tant que doublons ou parents orphelins sont non nuls.

## 6. Ledger du conducteur

Les observations et décisions sont écrites dans :

```text
conductor-ledger.jsonl
conductor-checkpoint.json
conductor-m-minus.jsonl
```

Le ledger garantit :

- séquence contiguë;
- déduplication par ID d’observation;
- hash individuel de chaque entrée;
- chaîne de hash cumulative;
- reprise après redémarrage;
- détection de modification rétrospective;
- checkpoint atomique;
- audit reproductible.

## 7. Synergie avec Ω-GENERATOR-DISCOVERY R0.4

Le moteur de campagnes génératives sait déjà planifier :

```text
1 179 648 000 ajouts logiques
1 000 époques
partitions déterministes
```

Le conducteur accepte ce manifeste et projette une boucle Ω8 par objet :

```text
1 179 648 000 sujets potentiels
× 8 événements
= 9 437 184 000 événements de workflow projetés
```

Cette projection n’écrit pas neuf milliards d’événements et ne prétend pas les avoir exécutés. Elle transforme une campagne de candidats en contrat explicite de capacité de validation et révèle le coût réel du passage :

```text
candidat généré
→ claim atomique
→ test discriminant
→ résultat
→ transition OAK
→ mémoire M⁻/M⁺
→ action suivante
```

## 8. Commandes

Planifier une enveloppe :

```bash
python -m omega_discovery_kernel_t.frontier_conductor plan \
  --wall-time-seconds 3600 \
  --writable-bytes 20000000000 \
  --rss-soft-bytes 2000000000 \
  --initial-events 1000000 \
  --growth-factor 2 \
  --bytes-per-event 160 \
  --throughput 20000 \
  --partition-events 250000 \
  --output generated/frontier-conductor-r0-4/plan.json
```

Évaluer une observation réelle :

```bash
python -m omega_discovery_kernel_t.frontier_conductor observe \
  --plan generated/frontier-conductor-r0-4/plan.json \
  --observation generated/frontier-conductor-r0-4/stage-0-observation.json \
  --ledger-dir generated/frontier-conductor-r0-4/ledger \
  --output generated/frontier-conductor-r0-4/stage-0-decision.json
```

Auditer le ledger :

```bash
python -m omega_discovery_kernel_t.frontier_conductor audit \
  --ledger-dir generated/frontier-conductor-r0-4/ledger
```

Projeter une campagne générative :

```bash
python -m omega_discovery_kernel_t.frontier_conductor project-generator \
  --campaign-summary generated/omega-generator-scale/billion-plan.json \
  --output generated/frontier-conductor-r0-4/generator-projection.json
```

## 9. Validation R0.4

La suite ciblée couvre :

- plan géométrique 1M, 2M, 4M, 8M;
- arrêt sur ressources réelles;
- alignement Ω8 de tous les stages et partitions;
- round-trip du manifeste;
- détection de falsification du plan;
- décisions EXPAND, RESHARD, HOLD, REDESIGN et STOP;
- création de M⁻ pour mémoire, latence, reprise, doublons et parents;
- ledger exactement-une-fois et hash-chaîné;
- détection de falsification du ledger;
- projection 1,179 milliard → 9,437 milliards d’événements;
- planification arithmétique au-delà d’un milliard sans matérialisation.

## 10. Frontières OAK

- Un événement de workflow n’est pas une observation scientifique.
- Une projection n’est pas une exécution.
- Une exécution n’est pas une validation externe.
- Un hash prouve l’intégrité relative des octets, pas la vérité du contenu.
- Une reprise n’est pas une réplication scientifique indépendante.
- Le volume n’augmente pas automatiquement la qualité de preuve.
- Les actions irréversibles restent soumises à approbation humaine, IPGate, sécurité, confidentialité et droit applicable.

## 11. Prochaine frontière

R0.5 devra remplacer la projection globale par une fédération de conducteurs :

```text
partitions indépendantes
→ leases et heartbeats
→ preuves Merkle de plage
→ agrégation hiérarchique
→ détection byzantine ou divergente
→ replay sélectif
→ calibration inter-machines
→ allocation Bayes-Tristan de ressources
```

La règle demeure : **plus ultra = plus prouvé, mieux mesuré, mieux repris et plus falsifiable — pas seulement plus grand.**
