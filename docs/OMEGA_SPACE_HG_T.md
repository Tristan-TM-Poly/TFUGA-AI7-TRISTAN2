# Ω-SPACE-HG-T∞ R0.1 MAX

## Hypergraphes fractals mycéliens des satellites, véhicules et modules spatiaux de Tristan

Ω-SPACE-HG-T∞ est une architecture de recherche logicielle pour représenter,
compiler, simuler, comparer et falsifier des systèmes spatiaux. La version R0.1
fournit un premier noyau vertical exécutable :

```text
intention de mission
→ manifeste typé
→ hypergraphe probatoire
→ orbite deux-corps
→ énergie + thermique + données
→ métriques CVCD réduites
→ exploration multiobjectif
→ front de Pareto
→ OAKBench
→ rapport reproductible
```

Le dépôt ne prétend pas produire un véhicule qualifié, une preuve scientifique,
un système de vol ni une nouvelle loi physique. Les résultats sont des sorties
de modèles réduits destinées au prototypage, à l'enseignement, à la comparaison
et à la préparation de modèles plus fidèles.

## 1. Objet central

Un système spatial est représenté par un hypergraphe :

\[
\mathcal H_{SPACE}=(V,E,\Theta,\Sigma,\Pi,\mathcal U,\mathcal P,\mathcal R)
\]

- `V` : missions, objectifs, exigences, véhicules, modules, sous-systèmes,
  logiciels, modèles, tests, preuves et risques;
- `E` : relations multiobjets d'énergie, chaleur, données, commandes, forces,
  couples, communications, dépendances et fautes;
- `Θ` : états physiques continus;
- `Σ` : modes, événements et états discrets;
- `Π` : politiques de contrôle, opérations, permissions et repli;
- `U` : incertitudes et domaines de validité;
- `P` : provenance, versions et preuves;
- `R` : exigences, contraintes, risques et décisions.

Chaque sortie JSON conserve un statut de revendication. R0.1 force :

```json
{
  "theorem_claimed": false,
  "flight_qualified_claimed": false,
  "scientific_validation_claimed": false
}
```

## 2. Caractère fractal et mycélien

La structure se répète à plusieurs échelles :

```text
programme
⊃ mission
⊃ flotte ou constellation
⊃ véhicule
⊃ module
⊃ sous-système
⊃ carte
⊃ composant
⊃ paramètre
⊃ preuve
```

Le caractère mycélien est représenté par les chemins alternatifs entre fonctions,
ressources et véhicules. R0.1 calcule un premier indicateur structurel de nœuds
fonctionnels uniques. Les versions suivantes devront ajouter arbres de fautes,
fiabilité dynamique, pannes communes, reconfiguration et migration de fonctions.

## 3. Atlas génératif

`omega_space_hg_t.atlas` fournit des taxonomies versionnées de :

- missions d'observation, communication, navigation, science et logistique;
- CubeSats, bus, essaims, plateformes, modules pressurisés et véhicules de surface;
- VLEO, LEO, SSO, MEO, GEO, cislunaire, Lagrange, surface et espace profond;
- charges utiles, structure, GN&C, énergie, thermique, données, propulsion,
  autonomie, sûreté, segment sol et fin de vie;
- niveaux de fidélité allant du budget symbolique aux données de vol.

Commande :

```bash
omega-space-hg atlas
```

L'atlas est une grammaire et non une liste d'engins validés. Son compteur
`cross_reference_cells` indique seulement la taille d'une table de références
croisées. Il ne représente ni des simulations exécutées ni des architectures
faisables.

## 4. Manifeste de mission

Le schéma `schemas/omega_space_mission_v1.schema.json` définit les entrées
minimales :

- objectif et durée;
- corps central et état orbital cartésien;
- masse, panneaux, batterie, charges et radiateur;
- génération, stockage et transmission de données;
- cycles de charge utile, liaison et éclipse;
- limites de revendication.

Scénario canonique :

```text
scenarios/omega_space_hg_t/leo_6u_observer.json
```

Validation et lecture :

```bash
python -m omega_space_hg_t.cli manifest --output /tmp/mission.json
python -m omega_space_hg_t.cli graph /tmp/mission.json --output /tmp/graph.json
```

## 5. Dynamique orbitale

R0.1 utilise le problème à deux corps :

\[
\ddot{\mathbf r}=-\mu\frac{\mathbf r}{\|\mathbf r\|^3}
\]

L'intégration emploie velocity-Verlet, choisi pour sa structure symplectique et sa
simplicité vérifiable. Les sorties incluent la dérive relative d'énergie spécifique.

Ce noyau n'inclut pas encore :

- aplatissement J2 et harmoniques;
- traînée atmosphérique;
- pression de radiation solaire;
- corps tiers;
- manœuvres finies;
- relativité;
- estimation d'orbite;
- analyse opérationnelle de conjonction.

Ces extensions devront être comparées à GMAT, Orekit ou une autre référence
indépendante avant promotion OAK.

## 6. Énergie, thermique et données

Le bilan énergétique réduit suit :

\[
E_{k+1}=\mathrm{clip}\left(E_k+
(P_{gen}-P_{load})\frac{\Delta t}{3600},0,E_{max}\right)
\]

Le nœud thermique suit :

\[
C\frac{dT}{dt}=Q_{interne}+Q_{solaire}+Q_{albedo}
-\epsilon\sigma A(T^4-T_{espace}^4)
\]

Le stockage suit génération et téléchargement selon un calendrier orbital
déterministe. Ces modèles servent à détecter rapidement :

- réserve de batterie insuffisante;
- température hors limites déclarées;
- saturation des données;
- couplages défavorables entre pointage, charge utile et liaison.

Ils ne remplacent pas un réseau thermique détaillé, un modèle de vieillissement,
un budget RF, une simulation d'antenne ni une analyse de composants.

## 7. Hypergraphe probatoire

Le compilateur produit des nœuds pour les sous-systèmes et exigences, puis des
hyperarêtes pour :

- énergie;
- thermique;
- données;
- contrôle et FDIR;
- cycle de vie;
- traçabilité objectif-exigence-sous-système.

Chaque graphe est sérialisé de manière déterministe et reçoit un SHA-256. Les
nœuds conservent `oak_status` et `evidence`. Une prochaine version ajoutera :

- unités et dimensions sur chaque port;
- versions des modèles;
- provenance de paramètres;
- matrices d'interface;
- liens vers essais et rapports;
- propagation d'incertitude;
- graphes de revendications et contre-preuves.

## 8. Frontière d'optimisation sans plafond arbitraire

`UnboundedDesignFrontier` associe chaque entier naturel à une architecture
déterministe par séquences radical-inverse. Les variables R0.1 sont :

- surface de panneau;
- capacité de batterie;
- surface de radiateur;
- cycle de charge utile.

La frontière n'a pas de plafond total permanent :

```json
{"permanent_total_cap": null}
```

Chaque exécution demeure bornée par `start_offset` et `count` :

```bash
omega-space-hg plan --start-offset 1000000 --count 10000
omega-space-hg optimize scenarios/omega_space_hg_t/leo_6u_observer.json \
  --start-offset 4096 --count 256
```

Le curseur `next_offset` permet de reprendre sans répéter les architectures.
L'absence de plafond logique n'implique jamais un calcul, une mémoire ou une
validation infinis.

## 9. Objectifs multiobjectifs

R0.1 minimise un vecteur transparent :

1. masse de conception approximative;
2. pénalité d'insécurité du modèle;
3. déficit de réserve énergétique;
4. occupation maximale du stockage;
5. dépassement thermique au-dessus de 300 K.

La masse est un proxy de phase préliminaire, non une nomenclature. Le front de
Pareto indique seulement les designs non dominés dans l'échantillon exécuté.

## 10. OAKBench

```bash
omega-space-hg oak
pytest -q tests/test_omega_space_hg_t.py
```

Les portes actuelles vérifient :

- dérive énergétique sur une orbite;
- intégrité de l'hypergraphe;
- réserves énergie et données;
- déterminisme exact;
- reprise de la frontière à grand indice;
- absence de revendication de preuve ou qualification.

Un résultat `passed=true` signifie seulement que ces fixtures logicielles ont
réussi dans cet environnement.

## 11. Commandes

```bash
omega-space-hg atlas
omega-space-hg manifest
omega-space-hg graph [mission.json]
omega-space-hg simulate [mission.json] --summary-only
omega-space-hg plan --start-offset 0 --count 128
omega-space-hg optimize [mission.json] --count 32
omega-space-hg oak
```

## 12. Intégrations prévues

Adaptateurs prioritaires :

- GMAT et Orekit pour l'orbite;
- Basilisk pour GN&C et simulation modulaire;
- cFS pour l'architecture logicielle de vol;
- CCSDS et XTCE pour paquets, télémesure et télécommande;
- SPICE pour géométrie et éphémérides;
- OpenMDAO ou équivalent pour MDO;
- outils FEM, thermique, RF et fiabilité selon licences et disponibilité.

Aucun adaptateur ne devra transformer une comparaison réussie en qualification
automatique.

## 13. Mémoire négative M⁻

- **M⁻ masse seule** : alléger un module peut détériorer énergie, thermique,
  contrôle et fiabilité.
- **M⁻ nominal seulement** : les moyennes cachent éclipses, pointes et pires cas.
- **M⁻ simulation = qualification** : une simulation réussie n'est pas un essai.
- **M⁻ pannes indépendantes** : les causes communes doivent être modélisées.
- **M⁻ autonomie sans enveloppe** : toute autonomie doit avoir permissions,
  interdictions, watchdog et repli.
- **M⁻ segment sol oublié** : mission = espace + sol + opérations + données.
- **M⁻ fin de vie reportée** : passivation et disposition sont des exigences de
  départ.
- **M⁻ atlas = accomplissement** : une classe ou combinaison indexée n'est pas
  un prototype ni une preuve.

## 14. Roadmap de fidélité

### R0.2 — Orbite et attitude

J2, traînée, SRP, quaternions, capteurs, roues, magnéto-coupleurs, estimation,
commande, jitter et saturation.

### R0.3 — Réseaux physiques

Réseau thermique multinœud, batterie vieillissante, EPS détaillé, budget de
liaison, files de données et fenêtres de stations sol.

### R0.4 — Fiabilité et autonomie

Fault trees, Monte-Carlo, fautes communes, FDIR, modes sûrs, reconfiguration et
mémoire M⁻ des anomalies.

### R0.5 — Constellations et espace distribué

Couverture, revisite, routage intersatellite, formation, essaim, allocation de
tâches, remplacement et déploiement progressif.

### R0.6 — Jumeau numérique et MBSE

Exigences, interfaces, modèles, essais, provenance, versions, coûts, risques et
preuves reliés dans un graphe exécutable.

### R1.0 — Validation externe

Comparaisons croisées publiées, jeux de données reproductibles, analyse
d'incertitude, documentation des écarts et pilotes avec équipes qualifiées.

## 15. Sécurité

Les travaux matériels à haute énergie, haute tension, pression, pyrotechnie,
propulsion, radiofréquence réglementée, laser puissant, source ionisante ou
système habité ne sont pas couverts par ce prototype. Ils exigent installations,
procédures, autorisations et personnel qualifiés.
