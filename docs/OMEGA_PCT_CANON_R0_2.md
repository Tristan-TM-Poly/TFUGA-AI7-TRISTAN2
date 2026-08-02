# Ω-PARTICULES-CHAMPS-T∞ — Canon exécutable R0.2

## 0. Position

Ω-PCT∞ est une architecture de recherche, de calcul et de falsification. Ce dépôt ne proclame ni nouvelle particule ni théorie finale. Son unité de progrès est un paquet vérifiable :

```text
définition → équation → code → test → observable → falsificateur → provenance → résidu
```

## 1. Constitution épistémique

Chaque objet porte un statut explicite : `established`, `effective`, `parametrization`, `hypothesis`, `exploratory`, `excluded` ou `unknown`. Un changement de statut exige une preuve versionnée. Les extensions HGFM, CVCD, FFWT, LOG/EXP et sédénioniques restent exploratoires tant qu'elles ne produisent pas de prédiction quantitative indépendante.

## 2. Ontologie

Le registre sépare : champ, excitation, particule fondamentale, composite, résonance, quasiparticule, soliton, défaut topologique, vide, événement, signal de détecteur, reconstruction et interprétation. Une trace instrumentale n'est pas automatiquement une particule; elle contribue à une inférence dépendant du modèle de détecteur.

## 3. Tenseur d'identité

Une identité particulaire contient au minimum masse ou dispersion, spin, charges, représentations de symétrie, largeur, durée de vie, composition, topologie, domaine d'échelle, environnement, incertitude et provenance. L'identité est un domaine de stabilité sous transformations, non une simple étiquette.

## 4. Hypergraphe particules–champs

Les champs, particules, interactions, expériences, paramètres, détecteurs et preuves sont des nœuds. Une interaction est une hyperarête orientée plusieurs-vers-plusieurs. Les médiateurs, couplages, ordres perturbatifs, hypothèses, domaines et résidus restent attachés à l'hyperarête.

## 5. Baseline physique

Le socle obligatoire est la théorie quantique des champs, le Modèle standard, la QED, la QCD, le secteur électrofaible, les oscillations des neutrinos, les théories effectives et la relativité générale dans leurs domaines testés. Toute extension Tristan doit retrouver ces limites ou expliquer quantitativement où et pourquoi elle s'en écarte.

## 6. Action et EFT

Un modèle calculable part d'une action, d'un Hamiltonien ou d'une dynamique effective explicite. Chaque opérateur doit déclarer sa dimension, son coefficient, son échelle de suppression, son statut et son domaine. Une correction HGFM/CVCD n'est pas une interaction physique tant qu'aucun terme dynamique et aucune observable ne sont définis.

## 7. Gates OAK

1. Définitions et types complets.
2. Dimensions et unités cohérentes.
3. Conditions initiales et aux limites.
4. Covariance appropriée au domaine.
5. Symétrie de jauge ou mécanisme de brisure explicite.
6. Hermiticité et positivité.
7. Causalité et unitarité lorsque requises.
8. Audit des anomalies.
9. Conservation ou violation calculée.
10. Limites connues retrouvées.
11. Stabilité numérique.
12. Paramètres identifiables.
13. Modèle de détecteur séparé.
14. Incertitudes et corrélations.
15. Falsificateur indépendant.
16. Contrôle négatif et baseline.
17. Mémoire M⁻ des faux signaux.
18. Rapport machine-readable.

## 8. Circuit de référence QED

Le processus `e⁻ μ⁻ → e⁻ μ⁻` réalise la première boucle complète : champs de Dirac, médiateur photonique, cinématique relativiste 2→2, invariants de Mandelstam, conservation, poids QED massless clairement borné, génération d'événements et rapport OAK. La singularité avant est bloquée plutôt que masquée.

## 9. Séparation théorie–détecteur

```text
symétrie → Lagrangien → amplitude → événement → réponse instrumentale
          → reconstruction → statistique → résidu → révision du modèle
```

Chaque niveau conserve ses hypothèses. Une reconstruction ne doit jamais réécrire silencieusement l'objet théorique.

## 10. Multi-échelle et FFWT

La couche FFWT/Haar agit sur les résidus, séries temporelles, cartes de calorimètres et topologies. Elle doit être comparée à des ondelettes classiques, statistiques standards et modèles d'apprentissage, avec données séparées, ablations, stabilité et coût mesuré. Un motif visuel ne constitue pas une découverte.

## 11. Sédénions OAK-safe

La couche Cayley-Dickson sert de laboratoire de représentation. Les audits obligatoires couvrent non-commutativité, non-associativité, dépendance au parenthésage, diviseurs de zéro, choix de base et projection réelle/complexe. Une composante algébrique ne devient une dimension physique qu'après définition covariante et prédiction testable.

## 12. Noether-Tristan

Le compilateur visé suit deux directions :

```text
symétrie → courant → charge → observable
résidu de conservation → brisure candidate → mécanisme → test
```

Il distingue symétrie exacte, approximative, émergente, spontanément brisée, explicitement brisée et simple régularité statistique.

## 13. Renormalisation HGFM

Les changements d'échelle deviennent un graphe versionné de théories, degrés de liberté, opérateurs, couplages, points fixes et erreurs de troncature. Une analogie entre domaines n'est promue que si les opérateurs et domaines correspondent, pas seulement la forme visuelle.

## 14. Mémoire négative M⁻

M⁻ enregistre l'hypothèse, la version, les données, la graine, l'environnement, le test échoué, le systématique identifié, la correction tentée et la condition de réouverture. Une anomalie disparue devient un anti-dataset plutôt que d'être oubliée.

## 15. Sans plafond arbitraire

Aucune constante `max_ajout` ne limite le nombre total de candidats. Le flux peut être infini; une exécution est néanmoins bornée par les ressources et la gouvernance : temps, mémoire, octets, quotas, coût, taux d'erreur, qualité, sécurité, propriété intellectuelle et rollback. Le contrôleur adapte les lots et checkpoint l'état.

## 16. Interprétation du front 100k+

Le front synthétique démontre une capacité logicielle, pas une découverte scientifique. Générer 10 000, 100 000 ou 10 millions d'objets augmente l'espace exploré; cela n'augmente pas automatiquement leur probabilité de vérité. La validation, la correction du multiple testing et la réplication doivent croître avec la génération.

## 17. Frontières de recherche

- masses, mélange et nature des neutrinos;
- confinement, hadrons, jets et QCD non perturbative;
- secteurs sombres et portails effectifs;
- gravité quantique et observables accessibles;
- topologie et phases émergentes;
- passage micro → méso → macro;
- calibration et reconstruction de détecteurs;
- recherche de résidus distribués sans gonflement statistique.

## 18. Machine d'état

```text
intuition
→ claim typé
→ modèle formel
→ équation
→ implémentation
→ test unitaire
→ benchmark
→ observable
→ modèle détecteur
→ comparaison aux données
→ réplication
→ canon candidat
```

Chaque transition possède un OAKGate. Une transition refusée produit une entrée M⁻ et une prochaine action.

## 19. Interfaces canoniques

- `FieldSpec`: champ et représentations.
- `ParticleSpec`: identité et provenance.
- `InteractionSpec`: hyperarête et conservations.
- `ModelRegistry`: registre validable.
- `ParticleFieldHypergraph`: projection JSON/GraphML.
- `OAKGate`: contrôles mathématiques et physiques.
- `OmegaPCTPipeline`: théorie → événements → rapports.
- `AdaptiveFrontier`: exploration sans plafond d'items.
- `JsonlLedger`: registre avec empreintes SHA-256.

## 20. Critère de révolution

Une extension est disruptive seulement si elle produit un gain mesuré : prédiction nouvelle, précision, vitesse, compression, explicabilité, interopérabilité, réduction d'erreur ou coût expérimental. Le nombre de lignes, de fichiers ou de candidats est une capacité, jamais une preuve.

## 21. Sorties reproductibles

```text
particle-field-hypergraph.json
particle-field-hypergraph.graphml
events.jsonl
oak-report.json
oak-report.md
manifest.json
checkpoint.json
M-minus.jsonl
```

## 22. Verrou final

Toute publication scientifique future doit versionner les données de référence, les constantes, les dépendances, les graines, les incertitudes, les comparaisons et les critères de rejet. Ω-PCT∞ demeure une architecture de recherche jusqu'à validation expérimentale indépendante.
