# Ω-HISTOSCI-HG-T∞

## Histoire hypergraphique de toutes les sciences de l’humanité — R0.1

> Chaque science est un réseau vivant de problèmes, observations, concepts,
> instruments, expériences, personnes, communautés, erreurs, institutions,
> applications et transformations sociales.

## Statut épistémique

Cette livraison est une **architecture logicielle et historiographique**. Elle ne
prétend pas constituer une histoire exhaustive, certifier la vérité de tous les
récits historiques, résoudre les controverses d’attribution ou représenter
complètement toutes les cultures. Le seed R0.1 contient surtout des
`SOFTWARE_FIXTURE` destinés à recevoir des sources primaires et des travaux
historiographiques qualifiés.

Invariants permanents :

```text
SOFTWARE_FIXTURE != HISTORICAL_TRUTH
SINGLE_SOURCE != ESTABLISHED_CONSENSUS
FAMOUS_PERSON != COMPLETE_CAUSAL_HISTORY
CHRONOLOGY != CAUSAL_HYPERGRAPH
EUROPEAN_CANON != GLOBAL_HISTORY_OF_SCIENCE
NUMERICAL_SCORE != HISTORIOGRAPHIC_PROOF
GENERATED_BRANCH != VERIFIED_HISTORICAL_BRANCH
```

## Objet fondamental

L’unité n’est ni une date isolée ni un « grand savant » isolé. C’est l’événement
épistémique contextualisé :

\[
E=(problème, observation, méthode, acteur, contexte, preuve, incertitude, conséquence).
\]

Une branche scientifique est une trajectoire multi-échelle :

\[
\mathcal{B}(t)=\{C_t,P_t,I_t,D_t,M_t,R_t,A_t\},
\]

où les composantes représentent concepts, problèmes, instruments, données,
méthodes, règles de preuve et applications/effets sociaux.

## Pourquoi un hypergraphe

Une chronologie simple produit `A → B → C`. Une transformation scientifique
réelle dépend souvent simultanément de plusieurs causes et produit plusieurs
conséquences :

\[
\{A,B,C,D\}\rightarrow E\rightarrow\{F,G,H\}.
\]

La spectroscopie, par exemple, est reliée à l’optique, la chimie, la
thermodynamique, l’électromagnétisme, la photographie, les détecteurs, les
mathématiques et la métrologie. Elle contribue ensuite à la mécanique quantique,
l’astrophysique, la chimie analytique, la médecine et la science des matériaux.

## Ontologie R0.1

### Nœuds

- observations, problèmes, concepts, hypothèses, modèles, théories et lois;
- expériences, instruments, matériaux, données et méthodes;
- personnes, communautés, institutions, lieux et langues;
- controverses, erreurs, applications, impacts et problèmes ouverts;
- branches, événements et sources.

### Hyperarêtes

Le moteur fournit notamment :

```text
influenced_by
enabled_by
measured_with
formalized_by
contradicted_by
corrected_by
split_into
merged_with
translated_through
independently_discovered
institutionalized_by
applied_to
misused_for
remains_open
refuted_by
not_reproduced_by
distorted_by
suppressed_or_forgotten_by
misattributed_to
enabled_exploitation
caused_unintended_harm
abandoned_for_lack_of_instrument
rediscovered_by
false_as_theory
fertile_for_method
```

Les relations négatives sont des objets de première classe. Une théorie peut être
fausse comme explication et néanmoins fertile pour l’instrumentation ou la
méthode.

## Couches temporelles

1. connaissances préhistoriques et incarnées;
2. civilisations anciennes;
3. réseaux savants médiévaux mondiaux;
4. sciences expérimentales et mathématisées;
5. industrialisation scientifique;
6. sciences du XXe siècle;
7. sciences numériques et massivement instrumentées;
8. science assistée par agents.

Ces couches ne sont pas une hiérarchie de valeur. Plusieurs traditions, langues
et communautés coexistent, interagissent, se perdent, se traduisent et se
redécouvrent.

## Couverture du seed

Le registre exécutable contient dix macro-familles :

- sciences formelles;
- physique;
- chimie;
- sciences de la Terre et de l’espace;
- sciences de la vie;
- médecine et santé;
- informatique et information;
- ingénieries;
- sciences humaines, sociales et comportementales;
- métasciences.

Elles sont déployées en 114 branches initiales. Ce nombre n’est ni un plafond ni
une mesure d’exhaustivité. `permanent_total_cap` est explicitement `null`, alors
que chaque campagne d’ingestion doit rester finie, reproductible et
checkpointable.

## Douze opérateurs d’évolution

1. observation;
2. classification;
3. instrumentation;
4. quantification;
5. formalisation;
6. expérimentation;
7. unification;
8. fragmentation;
9. transfert interdisciplinaire;
10. industrialisation;
11. crise;
12. reconstruction.

Une reconstruction scientifique ne supprime pas nécessairement les modèles
antérieurs. Elle peut en conserver les régimes de validité comme approximations.

## Mémoire négative M−

Chaque entrée conserve :

\[
M^-=(affirmation, plausibilité, test, échec, cause, leçon, risque\ de\ répétition).
\]

Catégories prioritaires :

- hypothèse réfutée;
- expérience non reproduite;
- erreur de calibration ou statistique;
- confusion corrélation-causalité;
- surajustement et artefact numérique;
- mauvaise attribution;
- fraude ou conflit d’intérêts;
- technologie dangereuse ou oppressive;
- exclusion de groupes;
- promesse industrielle non tenue;
- résultat réel avec interprétation fausse.

Le fixture spectroscopique encode l’erreur suivante : un petit résidu de fit ne
prouve pas l’identification physique unique des composantes. Les modèles
alternatifs, l’identifiabilité, les formes de raies, le bruit, les baselines et
les contrôles doivent être audités.

## Atlas polyglotte, mondial et décolonisé

Chaque événement historique doit pouvoir conserver :

- langue originale;
- lieu et communauté;
- tradition intellectuelle;
- canaux de transmission;
- traductions, pertes et transformations;
- attribution traditionnelle;
- attribution historiographique contestée;
- niveau de certitude;
- participation des artisans, techniciens, assistants, patients, navigateurs,
  agriculteurs, traducteurs et communautés locales.

`translated_through` doit pouvoir être aussi important que `discovered_by`.

## Score historique OAK

Le score logiciel combine qualité des sources, proximité des sources primaires,
corroboration indépendante, cohérence/reproductibilité et controverses non
résolues. Il classe provisoirement les assertions comme établies, probables,
contestées ou incertaines.

Le score n’est jamais une preuve automatique. Une assertion sans source est
plafonnée sous le statut établi, même si ses autres champs sont artificiellement
élevés.

## Architecture logicielle

```text
omega_histosci_hg_t/
├── models.py       # objets typés, statuts et empreintes canoniques
├── graph.py        # hypergraphe dirigé, requêtes et GraphML
├── registry.py     # branches, sources, événements et mémoire M−
├── oak.py          # score OAK explicite et prudent
├── seed.py         # 114 branches + fixture spectroscopique
├── report.py       # rapport déterministe et frontières épistémiques
└── cli.py          # audit, statistiques, lignage et export
```

Commandes :

```bash
omega-histoscience audit --output /tmp/audit.json
omega-histoscience stats
omega-histoscience list-branches --parent science.physics
omega-histoscience lineage physics.optics.spectroscopy
omega-histoscience export-graphml --output /tmp/histoscience.graphml
```

## Pipeline futur

```text
sources
→ extraction avec provenance
→ événements
→ entités
→ relations
→ controverses
→ validation OAK
→ tranches temporelles
→ récits conditionnés par le statut
```

Entrées futures : livres, articles, archives, catalogues d’instruments, brevets,
biographies, correspondances, bases bibliographiques, logiciels, jeux de données,
histoires orales et collections muséales.

Sorties : frises, hypergraphes interactifs, cartes géographiques, généalogies
d’instruments et d’équations, chemins problème→découverte→technologie et
erreur→correction→méthode.

## Connexion au corpus Tristan

Chaque branche Tristan doit pointer vers :

```text
ancêtres scientifiques
→ méthodes établies
→ combinaison proposée
→ extension spéculative
→ tests
→ résultats
→ mémoire négative
```

Les statuts « vision », « définition », « prototype », « simulation », « mesure »
et « preuve » restent séparés. Une visualisation, un grand graphe ou un score ne
transforme pas une hypothèse en loi scientifique.

## Gate R0.2

La version suivante exige au minimum :

1. ingestion de sources avec licence et provenance;
2. identifiants stables pour personnes, institutions, lieux et œuvres;
3. modèles d’attributions concurrentes;
4. dates incertaines et intervalles;
5. contrôle polyglotte;
6. premiers corpus sourcés pour spectroscopie, calcul, évolution et informatique;
7. tests adversariaux de biais géographique et de « grand homme »;
8. rendu narratif qui affiche explicitement les statuts contestés et incertains.

## Cristallisation

\[
Histoire\ scientifique = problèmes + observations + instruments + concepts + preuves + communautés + erreurs + impacts.
\]

\[
Science\ future = histoire\ traçable + mémoire\ négative + simulation + falsification + création.
\]
