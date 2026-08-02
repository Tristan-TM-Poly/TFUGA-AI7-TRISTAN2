# Analyse architecturale — Ω-WIKI-T∞ / Hypergraphe des connaissances utiles R0.2

**Statut OAK :** analyse structurée du corpus et de son architecture logicielle; aucune certification mathématique, physique, juridique, commerciale ou scientifique.

## 1. Diagnostic central

L'absorption R0.2 montre que le corpus TFUGA/AI-7 n'est pas une simple collection de théories isolées. Il possède une architecture récurrente :

```text
TFUGA -> HGFM -> CVCD
             |
             v
      hypothèses / modèles / artefacts
             |
             v
OAK <-> DCT-Ω / DCT++ <-> AI-7
 ^                           |
 |                           v
Bayes-Tristan <-> FailureSynth
             |
             v
        nouveau cycle
```

La chaîne fondamentale peut être résumée ainsi :

```text
générer -> représenter -> compresser -> décompresser -> tester -> mémoriser -> réviser
```

Cette structure traverse les branches mathématiques, physiques, logicielles, cognitives, institutionnelles et économiques.

## 2. Rôle des noyaux

### TFUGA

Racine générative du corpus. TFUGA produit l'espace des objets, transformations, hypothèses et architectures candidates.

**Risque :** expansion conceptuelle sans formalisation ni test.

### HGFM

Couche de représentation hypergraphique. HGFM permet de représenter plusieurs types de nœuds et des relations multi-objets sans forcer une hiérarchie linéaire unique.

**Risque :** métaphore riche mais schéma insuffisamment contraint.

### CVCD

Couche de compression et de décompression. CVCD cherche des invariants fertiles, réduit la redondance et régénère des modèles, variantes ou expériences.

**Risque :** confondre reconstruction plausible, généralisation, hallucination et preuve.

### OAK

Couche de falsification, statut et promotion. OAK empêche qu'une idée, une simulation ou une coïncidence numérique soit automatiquement promue en résultat établi.

### DCT-Ω / DCT++

Contrat de preuve minimal : document, code, test, données, risque, éthique, statut, prochaine action et liens.

### AI-7

Métabolisme opérationnel qui produit, vérifie, teste, intègre, documente et canonise les artefacts.

### Bayes-Tristan

Couche d'actualisation des priorités et croyances à partir des résultats, résidus et nouvelles preuves.

### FailureSynth

Mémoire négative. Les échecs, contre-exemples et surpromesses deviennent des contraintes réutilisables plutôt que des erreurs oubliées.

## 3. Ce que R0.2 accomplit réellement

R0.2 transforme trois sources canoniques en un hypergraphe reproductible de :

- **92 nœuds purifiés**;
- **94 hyperarêtes**;
- systèmes, couches, risques, actions, chemins GitHub et étapes du pipeline;
- relations explicites issues des documents;
- relations transversales marquées comme interprétations candidates;
- identifiants déterministes et provenance conservée.

Le passage de 96 à 92 nœuds après purification a supprimé des pseudo-entités produites par des lignes `Nom: rôle`, sans réduire le nombre d'hyperarêtes utiles. C'est un exemple concret de compression fertile : moins de bruit, même pouvoir relationnel.

## 4. Ce que R0.2 n'est pas encore

Le graphe répond surtout aux questions :

```text
Qu'est-ce qui existe?
Où est-ce stocké?
Quel est son statut?
Quel est son risque?
Quelle est la prochaine action?
```

Il ne répond pas encore complètement à :

```text
Quelle affirmation précise est faite?
Quelles hypothèses la conditionnent?
Quelle équation la formalise?
Quel code l'implémente?
Quel test la vérifie?
Quelle mesure la soutient?
Quel contre-exemple la limite?
Quelle source externe la contextualise?
```

R0.2 est donc un **squelette cognitif traçable**, pas encore un cerveau épistémique complet.

## 5. Faiblesse structurelle principale

La densité du graphe ne doit pas croître plus vite que sa densité de preuve.

Ajouter des milliers de nœuds et de relations sans ajouter de tests, mesures, sources ou contre-exemples créerait une fausse densité : un graphe impressionnant mais peu fiable.

Règle proposée :

> Croissance presque sans plafond des candidats; croissance strictement gagnée du canon par provenance, formalisation, test, mesure, contre-exemple et revue.

## 6. Cellule de connaissance cible

Chaque théorie ou module important devrait converger vers une cellule complète :

```yaml
id: stable identifier
name: canonical name
aliases: []
definition: precise definition
domain: []
status: OAK status
claims: []
hypotheses: []
objects: []
operators: []
equations: []
source_documents: []
external_sources: []
code_paths: []
test_paths: []
datasets: []
measurements: []
results: []
counterexamples: []
risks: []
m_minus: []
uncertainty: {}
next_action: smallest falsifiable step
```

## 7. Hyperarêtes prioritaires pour R0.3

R0.3 devrait ajouter les types de relations suivants :

```text
claim_defined_by_equation
claim_requires_hypothesis
claim_implemented_by_code
claim_tested_by_test
claim_evaluated_on_dataset
claim_supported_by_result
claim_limited_by_counterexample
claim_contradicted_by_result
claim_measured_by_instrument
claim_cites_external_source
claim_supersedes_claim
claim_refines_claim
artifact_generated_from_claim
failure_updates_oak_gate
```

Ces hyperarêtes feront passer le graphe de la navigation à l'épistémologie exécutable.

## 8. Alias et identité sémantique

Le corpus emploie plusieurs noms proches ou historiques. Une fusion automatique serait dangereuse; une séparation permanente produirait des doublons.

Relations nécessaires :

```text
exact_alias
probable_alias
historical_name
specializes
extends
overlaps_with
not_equivalent_to
supersedes
```

Chaque fusion d'identité doit conserver l'ancien nom, sa provenance et la raison de la décision.

## 9. Temporalité

Le futur hypergraphe doit devenir temporel :

- apparition d'une théorie;
- modification de définition;
- expérience ayant changé son statut;
- branche remplacée ou archivée;
- échec ayant créé une règle M-;
- commit, PR ou publication correspondant à la transition.

Une transition OAK devrait devenir un événement explicite :

```text
FORMALIZED --test:T123--> TESTED_LOCAL
TESTED_LOCAL --counterexample:C17--> REFUTED
REFUTED --revision:R4--> FORMALIZED
```

## 10. Utilité multidimensionnelle

Le score scalaire actuel reste un outil de navigation. La prochaine version devrait conserver un vecteur :

```text
maturity
falsifiability
reproducibility
reuse
scientific_value
product_value
cost
risk
uncertainty
maintenance_load
```

Aucune composante ne doit être interprétée comme probabilité de vérité ou valeur financière certifiée.

## 11. Noyaux les plus immédiatement exploitables

### OAK + DCT-Ω

Infrastructure transversale pouvant gouverner toutes les branches.

### FFWT-HAC-CVCD

Branche scientifique avec baselines, signaux, métriques et conditions d'échec mesurables.

### Ω-LIN-T

Bon candidat de publication/prototype grâce aux domaines de validité et résidus explicites.

### AUTO²

Moteur d'exécution contrôlée : intention, permissions, dry-run, action, observation, rollback et mémoire.

### DeepTech Forge

Pont recherche -> prototype -> IP -> offre, à condition de conserver les distinctions :

```text
idée != invention brevetable
prototype != produit
intérêt != client
valeur simulée != revenu
```

## 12. Priorités R0.3

1. Ajouter les nœuds `claim`, `equation`, `code`, `test`, `dataset`, `result`, `measurement`, `counterexample`.
2. Construire la première cellule complète sur **FFWT-HAC-CVCD**.
3. Construire une deuxième cellule sur **Ω-LIN-T** afin de tester la généralité du schéma.
4. Ajouter un registre temporel des transitions OAK.
5. Ajouter l'alignement d'alias avec décisions traçables.
6. Enrichir chaque noyau avec Wikipédia/Wikidata, DOI, arXiv, ISBN, standards et dépôts externes.
7. Générer une file d'action : P0 tests bloquants, P1 prototypes proches, P2 preuves manquantes, P3 enrichissement, P4 backlog, P5 archive/quarantaine.

## 13. Critères d'acceptation R0.3

R0.3 est réussi si au moins une théorie possède une chaîne entièrement navigable :

```text
definition
-> claim
-> hypotheses
-> equation/model
-> code
-> test
-> dataset
-> result
-> counterexample or limitation
-> OAK status transition
-> next experiment
```

Le tout doit être reproductible, exportable en JSON/JSONL/GraphML et vérifié par tests hors réseau.

## Conclusion

R0.2 prouve surtout que le corpus peut être converti en infrastructure cognitive sans perdre ses statuts, risques et prochaines actions.

La prochaine avancée n'est pas simplement d'ajouter davantage de théories. Elle consiste à transformer les nœuds principaux en cellules de connaissance capables de relier affirmation, preuve, code, test, mesure, contre-exemple, incertitude et décision OAK.

À ce stade, l'hypergraphe ne représentera plus seulement le corpus : il deviendra le moteur qui le produit, le falsifie, le corrige et le fait évoluer.
