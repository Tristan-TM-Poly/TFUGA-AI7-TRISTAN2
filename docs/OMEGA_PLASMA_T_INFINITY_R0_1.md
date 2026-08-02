# Ω-PLASMA-T∞ — Canon logiciel R0.1

**Statut :** infrastructure de recherche OAK-safe, simulation-first et explicitement non certifiée pour le contrôle matériel.

## 1. Mission

Ω-PLASMA-T∞ relie dans une représentation commune :

- espèces chargées, neutres, moléculaires, poussiéreuses et collectives;
- distributions cinétiques, moments fluides et champs électromagnétiques;
- collisions, réactions, rayonnement, surfaces et géométrie;
- régimes classiques, quantiques, relativistes et fortement couplés;
- diagnostics, modèles numériques, résidus et incertitudes;
- atlas, campagnes, OAKBench et mémoire négative M⁻.

Le dépôt ne prétend pas fournir un solveur universel. Il construit le **compilateur de régime** qui choisit et audite les descriptions candidates.

## 2. Statuts épistémiques

- **P0 — établi :** Maxwell, cinétique, Vlasov, Boltzmann, fluides, MHD, collisions et physique atomique dans leurs domaines connus.
- **P1 — numérique établi :** PIC, MCC, MHD, Hall-MHD, gyrocinétique, hybrides et cinétique quantique selon les hypothèses déclarées.
- **P2 — extension Tristan :** classification hypergraphique, compilateur de modèles, atlas multi-régime, OAKGate et campagnes adaptatives.
- **P3 — hypothèse fertile :** CVCD/FFWT pour précurseurs d’instabilité, conception inverse et transitions automatiques entre modèles.
- **P4 — spéculatif :** toute extension hyperalgébrique sans gain quantitatif démontré.

Aucun nom, score ou graphique ne constitue une preuve.

## 3. État universel

Un état logiciel contient :

```text
species[]
geometry
magnetic_field_t
electric_field_v_m
ionization_fraction
pressure_pa
radiation_energy_density_j_m3
relativistic_bulk_gamma
requested_observables[]
metadata
```

Chaque espèce porte au minimum charge, masse, densité, température, fréquence collisionnelle et vitesse de dérive.

## 4. Invariants calculés

Le noyau calcule ou approxime :

- longueur et nombre de Debye;
- fréquence plasma et profondeur de peau électronique;
- fréquences cyclotron et rayons de Larmor;
- vitesse thermique et libre parcours moyen;
- magnétisation Ωc/ν et nombre de Knudsen;
- paramètre de couplage Γ;
- bêta plasma;
- non-neutralité;
- ratio de dégénérescence de Fermi;
- ratio thermique relativiste;
- vitesses d’Alfvén et ion-acoustique;
- proxy de Reynolds magnétique.

Toutes les approximations sont exposées dans le rapport.

## 5. Classificateur multi-label

Un plasma peut être simultanément :

```text
collectif + faiblement couplé + partiellement ionisé
+ électrons magnétisés + ions transitionnels
+ hors équilibre thermique + couplé aux surfaces
```

Le classificateur n’écrase donc pas la physique dans une seule étiquette. Chaque label contient sa règle, sa valeur et un niveau de confiance.

## 6. Compilateur de modèles

Vingt-deux familles initiales sont comparées :

- chimie globale;
- drift-diffusion;
- MHD idéale/résistive et Hall-MHD;
- deux-fluides et multi-fluides;
- Vlasov–Poisson et Vlasov–Maxwell;
- PIC électrostatique, électromagnétique et PIC-MCC;
- hybride ions cinétiques/électrons fluides;
- gyrocinétique;
- hydrodynamique quantique et Wigner–Poisson;
- MHD radiative;
- PIC relativiste;
- plasma poussiéreux;
- gaine et réactions de surface;
- équation d’état de matière dense chaude.

Chaque candidat est `recommended`, `conditional` ou `rejected`, avec raisons, bloqueurs et extensions requises.

## 7. Atlas initial

Le noyau source contient 29 régimes parents :

1. décharge froide basse pression;
2. plasma froid atmosphérique;
3. arc thermique;
4. cœur tokamak;
5. bord tokamak et SOL;
6. stellarator;
7. miroir magnétique;
8. configuration à champ inversé;
9. Z-pinch;
10. confinement inertiel;
11. wakefield laser;
12. matière dense chaude;
13. plasma ultrafroid;
14. plasma poussiéreux;
15. plasma électron-positron;
16. plasma non neutre;
17. couronne solaire;
18. vent solaire;
19. magnétosphère;
20. ionosphère;
21. disque d’accrétion;
22. plasma de pulsar;
23. milieu interstellaire;
24. propulseur Hall;
25. propulseur ionique;
26. propulseur magnétoplasmadynamique;
27. plasma électron-trou;
28. gaz de plasmons de surface;
29. plasma quarks-gluons.

Le chargeur crée trois spécialisations supplémentaires par régime — collisionless, collisional et magnetized — soit **116 régimes adressables**.

## 8. Espace sans plafond fixe

Les axes initiaux sont :

```text
coupling:       weak | moderate | strong
collisionality: collisionless | transitional | collisional
magnetization:  unmagnetized | partially_magnetized | magnetized
statistics:     classical | degenerate
relativity:     nonrelativistic | relativistic
```

Le produit donne 108 cellules par régime et **12 528 cellules** pour R0.1.

Ce nombre est un état de l’atlas, pas un plafond permanent. L’itérateur est paresseux; de nouveaux axes ou régimes augmentent l’espace sans changer une constante maximale.

## 9. Instabilités

L’atlas couvre quarante familles, notamment :

- two-stream, bump-on-tail, Buneman et ion-acoustique;
- Weibel, filamentation, firehose et mirror;
- drift-wave, lower-hybrid drift et diocotron;
- kink, sausage, tearing, plasmoid et interchange;
- ballooning, Rayleigh–Taylor et Kelvin–Helmholtz;
- Raman, Brillouin, modulational et parametric decay;
- ELM, sawtooth, neoclassical tearing et resistive-wall;
- MRI, instabilité thermique/radiative et cosmic-ray streaming;
- fronts d’ionisation, striations, gaines et modes poussiéreux.

Chaque entrée exige un moteur, des diagnostics et des contrôles négatifs.

## 10. Diagnostics

Trente diagnostics initiaux relient mesure, inversion, incertitudes et contrôles OAK : sondes, analyseurs d’énergie, interférométrie, diffusion Thomson/Raman, LIF, spectroscopie, bolométrie, imagerie, réflectométrie, ECE, CXRS, MSE et suivi de poussières.

## 11. OAKGate

Le rapport bloque les entrées invalides et signale :

- collectivité insuffisante;
- longueur de Debye non résolue;
- fermeture gaz idéal incompatible avec Γ;
- besoin de fermeture quantique;
- besoin de gaine et de boucle plasma–surface;
- cible ou tolérance non spécifiée;
- contradictions de classification.

La promotion exige ensuite conservation, positivité, convergence, baseline, incertitude et contrôles négatifs.

## 12. M⁻ — mémoire négative

Les échecs à enregistrer comprennent :

- chauffage numérique et diffusion artificielle;
- faux modes dus au maillage ou aux frontières;
- sous-échantillonnage particulaire;
- violation de ∇·B ou de la loi de Gauss;
- modèle fluide appliqué à une distribution non locale;
- MHD appliquée sous les échelles inertielles pertinentes;
- réaction ou espèce absente;
- inversion diagnostique non identifiable;
- corrélation visuelle prise pour découverte;
- gain apparent obtenu par changement de métrique.

## 13. Campagnes

`CampaignGenerator` consomme un produit cartésien paresseux, écrit en JSONL, produit des checkpoints et accepte un budget d’exécution optionnel.

Un `work_budget` borne une expérience réelle. Il ne devient jamais une limite architecturale permanente.

## 14. Interfaces Tristan

- Ω-PFT-T : fluides, MHD, turbulence et frontières;
- Ω-TRANSFORM-T : FFWT, spectres et détection multi-échelle;
- Ω-VTP-T : vectorisation, GPU et calcul distribué;
- Ω-SOLID-T∞ : plasma–surface, plasmons et matière condensée;
- Ω-OEMMTD-T : conversion opto-électro-magnéto-mécano-thermique;
- Bayes-Tristan : postérieurs de modèles et de diagnostics;
- Ω-UNC²-T : incertitude et méta-incertitude;
- Ω-AUTO²-T : campagnes, checkpoints et régénération;
- Ω-SANS-PLAFOND-T∞ : découverte adaptative des limites réelles.

## 15. Contrat de sécurité

Ce dépôt n’autorise pas automatiquement :

- haute tension, forts courants ou vide;
- gaz toxiques/réactifs;
- lasers intenses, UV, rayons X ou sources ionisantes;
- réacteurs de fusion ou dispositifs nucléaires;
- propulseurs ou bancs de puissance;
- contrôle matériel ou médical;
- qualification industrielle.

Les sorties sont des objets de recherche et de planification expérimentale à réviser par des professionnels compétents.

## 16. OAKBench R0.1

Trente benchmarks sont catalogués, des oscillations plasma et de l’écrantage de Debye jusqu’à la reconnexion GEM, Orszag–Tang, Brio–Wu, Weibel, chimie globale, matière dense et symétrie des plasmas de paires.

Chaque benchmark conserve : erreur, résidu de conservation, résolution, temps, reproductibilité, référence et contrôle négatif.

## 17. Démonstration vérifiée

Le paquet R0.1 a passé localement :

```text
15 tests unitaires
compilation Python
évaluation CLI d’un plasma argon partiellement ionisé
campagne de 600 configurations
itération complète des 12 528 cellules de régime
```

Ces résultats certifient le fonctionnement logiciel ciblé, pas la validité universelle des modèles physiques.

## 18. Prochaines cristallisations

1. solveur Vlasov–Poisson 1D de référence;
2. PIC électrostatique déterministe avec bilan énergétique;
3. MHD 1D/2D avec nettoyage de divergence;
4. chimie argon documentée avec provenance des taux;
5. gaine de Bohm/Child–Langmuir;
6. benchmark Landau et two-stream;
7. FFWT des précurseurs d’instabilité;
8. assimilation multi-diagnostic Bayes-Tristan;
9. transitions cinétique ↔ fluide avec résidu explicite;
10. planification distribuée de millions de cas par sharding et backpressure.

## 19. Formule canonique

```text
Ω-PLASMA-T∞
= état typé
+ invariants physiques
+ classification multi-label
+ compilateur de modèles
+ atlas de régimes/instabilités/diagnostics
+ HGFM
+ OAKGate
+ campagnes sans plafond arbitraire
+ M⁻
```

Une extension n’est promue que si elle améliore une prédiction, une reconstruction, une stabilité, une efficacité ou une décision tout en conservant unités, domaine, résidus et possibilité de falsification.
