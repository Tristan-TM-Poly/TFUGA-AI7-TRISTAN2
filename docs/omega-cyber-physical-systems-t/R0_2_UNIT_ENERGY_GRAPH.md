# Ω-CYBER-PHYSICAL-SYSTEMS-T∞ R0.2

## UnitGraph-T × EnergyGraph-T

R0.2 ajoute une couche de cohérence dimensionnelle, de causalité des interfaces et de comptabilité énergétique à tous les prototypes cyberphysiques de Tristan.

Cette couche vise les systèmes qui combinent plusieurs domaines : mécanique translationnelle ou rotationnelle, puissance électrique, électronique, thermique, fluides, contrôle, logiciel et données.

Elle ne transforme pas une simulation en preuve physique. Elle vérifie que les unités, les connexions et les bilans déclarés sont cohérents avec les modèles logiciels exécutés.

---

## 1. UnitGraph-T

### 1.1 Vecteur dimensionnel

Chaque unité est représentée par les sept dimensions SI de base :

```text
masse, longueur, temps, courant, température,
quantité de matière, intensité lumineuse
```

Une unité dérivée devient un vecteur d’exposants. Par exemple :

```text
W = M¹ L² T⁻³
V = M¹ L² T⁻³ I⁻¹
A = I¹
N = M¹ L¹ T⁻²
Pa = M¹ L⁻¹ T⁻²
```

Le registre R0.2 couvre notamment :

- seconde, hertz, mètre, millimètre, kilogramme;
- ampère, volt, ohm, henry, coulomb;
- newton, newton-mètre, joule, watt, pascal;
- rad/s, rpm, m/s;
- m³/s et L/min;
- kelvin et W/K;
- échantillons/s et bits/s comme dimensions informationnelles non physiques.

### 1.2 Paires effort–flux

UnitGraph vérifie les paires de puissance suivantes :

```text
translation : force × vitesse
rotation    : couple × vitesse angulaire
électrique  : tension × courant
hydraulique : pression × débit volumique
thermique   : température × débit d’entropie
```

Les ports logiciel, données et signaux électroniques sont classés comme canaux informationnels non énergétiques.

### 1.3 Sémantique thermique explicite

Le blueprint R0.1 utilise actuellement :

```text
effort = K
flow   = W
```

Cette paire ne forme pas un produit de puissance, puisque le flux est déjà une puissance thermique.

R0.2 ne masque pas cette différence. Le port est classé :

```text
direct_power_flow
```

avec l’avertissement :

```text
thermal_heat_rate_used_instead_of_entropy_flow
```

Une représentation strictement conjuguée utiliserait un flux de type W/K.

### 1.4 Connexions et causalité

Pour chaque connexion, UnitGraph vérifie :

- compatibilité dimensionnelle des efforts;
- compatibilité dimensionnelle des flux;
- facteur de conversion d’échelle;
- causalité sortie → entrée;
- domaine partagé;
- nécessité éventuelle d’un adaptateur explicite.

Une compatibilité dimensionnelle ne prouve pas la calibration, la polarité, la convention de signe ou l’exactitude physique.

---

## 2. EnergyGraph-T

EnergyGraph audite une trajectoire produite par `WholeSystemCoSim-T`.

### 2.1 Termes suivis

Le rapport nominal contient :

- énergie électrique fournie;
- variation d’énergie magnétique de l’inductance;
- pertes cuivre I²R;
- conversion électromagnétique;
- puissance mécanique transmise;
- résidu de conversion;
- variation d’énergie cinétique;
- variation d’énergie élastique;
- pertes visqueuses;
- travail contre la charge externe;
- variation d’énergie thermique;
- refroidissement vers l’environnement;
- sortie non suivie optionnelle pour tests adversariaux.

### 2.2 Bilans séparés

Quatre bilans sont calculés.

#### Électrique

```text
énergie source
≈ variation magnétique + pertes cuivre + conversion électromagnétique
```

#### Thermique

```text
pertes cuivre
≈ variation thermique + refroidissement
```

#### Mécanique

```text
énergie mécanique délivrée
≈ variation cinétique + variation élastique
  + pertes visqueuses + travail externe
```

#### Global

Les termes de conversion intermédiaires sont éliminés afin d’éviter le double comptage.

```text
source électrique
≈ stockages finaux + dissipations + travail externe
  + résidu de conversion + sorties non suivies
```

### 2.3 Résidu et tolérance

Chaque bilan conserve :

- énergie fournie;
- énergie comptabilisée;
- résidu signé;
- résidu normalisé;
- tolérance en joules;
- verdict logiciel.

La tolérance est :

```text
max(tolérance minimale, fraction × référence énergétique)
```

Le défaut R0.2 est de 2 % avec un minimum de 0,02 J.

Cette tolérance couvre l’intégration trapézoïdale, l’échantillonnage fini et les simplifications du modèle. Elle n’est pas une incertitude métrologique.

---

## 3. Passivité

R0.2 inspecte :

- positivité des pertes cuivre;
- positivité des pertes visqueuses;
- positivité du refroidissement;
- signe du résidu de conversion;
- éventuelle énergie créée apparente.

Les classes possibles incluent :

```text
PASSIVE_WITHIN_DECLARED_LUMPED_MODEL
INCONCLUSIVE_BIDIRECTIONAL_CONVERSION
NEGATIVE_DISSIPATION_CANDIDATE
RESIDUAL_EXCEEDS_TOLERANCE
```

Même lorsque le modèle est classé passif dans la fixture, le rapport conserve :

```text
passivity_proven: false
physical_validation: false
```

La passivité réelle exigerait une formalisation plus complète, des conventions de ports cohérentes, des paramètres validés et des essais.

---

## 4. Test adversarial

EnergyGraph accepte une quantité explicite `untracked_output_energy_j` destinée aux tests.

La fixture OAK ajoute artificiellement :

```text
5 J de sortie non suivie
```

Le bilan global doit alors échouer.

Ce test démontre que le système ne valide pas automatiquement toute trajectoire produite par le simulateur.

---

## 5. OAKBench R0.2

Les gates sont :

1. registre d’unités et conversion rpm → rad/s;
2. pression × débit volumique = dimension de puissance;
3. absence d’unité inconnue dans le blueprint;
4. causalité et compatibilité des six connexions;
5. avertissement thermique conservé;
6. fermeture nominale des quatre bilans;
7. scénario fauté toujours auditable;
8. rejet de la sortie énergétique adversariale;
9. déterminisme SHA-256;
10. absence d’auto-certification.

Statut possible :

```text
CERTIFIED_COMPUTATIONAL_UNIT_ENERGY_GRAPH_R0_2
```

Ce statut signifie uniquement que les invariants logiciels testés passent.

---

## 6. Interfaces

```bash
omega-cps-r02 benchmark
omega-cps-r02 unit-demo
omega-cps-r02 energy-demo --summary-only
omega-cps-r02 energy-demo --faulted --summary-only
omega-cps-r02 energy-demo --untracked-output-j 5
omega-cps-r02 convert 60 rpm rad/s
omega-cps-r02 convert 60 L/min m^3/s
```

---

## 7. Contrats JSON

```text
schemas/cyber_physical_unit_graph_r02.schema.json
schemas/cyber_physical_energy_graph_r02.schema.json
```

Les schémas imposent notamment :

- hashes SHA-256;
- certificats physiques faux;
- passivité non prouvée;
- conservation non prouvée;
- matériel non validé;
- résultats et résidus numériques explicites.

---

## 8. Limites

R0.2 ne démontre pas :

- l’exactitude physique des modèles;
- la conservation énergétique d’un prototype réel;
- la stabilité globale;
- la passivité formelle;
- les effets de commutation;
- les pertes magnétiques détaillées;
- le frottement sec, jeu, hystérésis ou flexibilité;
- la précision des paramètres thermiques;
- la compatibilité EMC;
- la sécurité fonctionnelle;
- la conformité à une norme.

---

## 9. Suite

R0.3 doit ajouter :

- automates hybrides;
- gardes, invariants et transitions;
- propriétés temporelles;
- détection de Zeno;
- reachability bornée;
- contrats de sûreté et de vivacité;
- scénarios de repli et états sûrs.

R0.4 doit préparer les adaptateurs FMI/FMU, Modelica, SPICE, ROS 2, CAN et OPC-UA, sans simuler une intégration externe qui n’a pas réellement été exécutée.
