# Ω-CYBER-PHYSICAL-SYSTEMS-T∞ R0.1

## Système d’exploitation des prototypes mécaniques, électriques, électroniques et logiciels de Tristan

### Statut

```text
COMPUTATIONAL_RESEARCH_ARCHITECTURE
```

Ω-CYBER-PHYSICAL-SYSTEMS-T∞ généralise les travaux propulsion vers tous les systèmes où matière, énergie, mouvement, capteurs, commande, logiciel et données interagissent.

Le noyau R0.1 est exécutable et falsifiable. Il ne constitue pas une certification physique, logicielle, fonctionnelle, industrielle ou réglementaire.

---

## 1. Portée

Le système vise notamment :

- mécanismes et machines;
- axes linéaires et rotatifs;
- moteurs, générateurs et transmissions;
- robots, manipulateurs et véhicules;
- pompes, vannes, compresseurs et skids fluidiques;
- batteries, convertisseurs, BMS et boucles thermiques;
- électronique de puissance;
- capteurs, ADC, DAC, PWM et télémétrie;
- microcontrôleurs, FPGA, automates et calculateurs;
- contrôle temps réel;
- logiciels embarqués;
- bancs instrumentés;
- systèmes manufacturiers;
- instruments scientifiques;
- propulsion aérienne, marine ou terrestre comme sous-système d’un véhicule complet;
- jumeaux numériques et campagnes d’essais.

La propulsion R0.1–R0.5 demeure compatible avec ce cadre, mais elle n’est plus le centre de l’architecture générale.

---

## 2. Objet central : `SystemBlueprint`

Chaque prototype devient un graphe typé :

```text
SystemBlueprint
├── Components
├── Ports
├── Connections
├── InterfaceContracts
├── Requirements
├── FaultModes
├── Evidence
└── LifecycleStage
```

Un composant peut appartenir à plusieurs domaines :

```text
mechanical_translational
mechanical_rotational
electrical_power
electronic_signal
thermal
fluid
software
data
```

### Exemple

Une chaîne d’axe électromécanique est représentée comme :

```text
DC Bus
  └─electrical_power→ Motor Drive
       ├─electrical_power→ DC Motor
       └─electronic_signal← Real-Time Controller
                              ↑
                              └─electronic_signal← Encoder

DC Motor
  └─mechanical_rotational→ Ball Screw
       └─mechanical_translational→ Linear Load
```

Les conversions de domaine appartiennent aux composants. Une connexion relie deux ports du même domaine. Cette règle empêche de masquer une conversion physique derrière une simple arête abstraite.

---

## 3. Contrats d’interface

Chaque port déclare :

- un identifiant;
- un domaine;
- une direction;
- une variable d’effort;
- une variable de flux;
- une unité pour chaque variable;
- une capacité facultative.

Exemples :

| Domaine | Effort | Flux |
|---|---|---|
| translation | force `N` | vitesse `m/s` |
| rotation | couple `N·m` | vitesse `rad/s` |
| puissance électrique | tension `V` | courant `A` |
| thermique | température `K` | chaleur `W` |
| fluide | pression `Pa` | débit `m³/s` |
| signal | amplitude `V` | échantillons/s |
| données | valeur | bits/s |

Cette représentation prépare des vérifications futures de puissance, causalité, unités, conservation et passivité.

---

## 4. DynamicsKernel-T

R0.1 fournit des modèles déterministes de référence :

### Mécanique translationnelle

```text
m x¨ + c x˙ + k x = F
```

### Moteur DC électromécanique

```text
L i˙ = V - R i - K_e ω
J ω˙ = K_t i - bω - τ_load
```

### Axe électromécanique rigide

```text
m x¨ = K_t i n η - c x˙ - kx - F_ext
L i˙ = V - Ri - K_e n x˙
```

avec :

- `n` : conversion rad moteur par mètre;
- `η` : efficacité de transmission;
- `i` : courant;
- `x` : position de charge.

L’intégrateur RK4 est déterministe et produit un hash SHA-256 de la trajectoire.

### Limites R0.1

Les modèles n’incluent pas automatiquement :

- jeu mécanique;
- friction de Coulomb;
- saturation magnétique;
- commutation;
- modes flexibles;
- hystérésis;
- turbulences;
- vieillissement;
- incertitude de fabrication;
- couplages électromagnétiques complets.

Ils servent à valider les contrats logiciels et l’architecture de preuve avant l’introduction de solveurs spécialisés.

---

## 5. ControlKernel-T

Le PID R0.1 comprend :

- saturation de sortie;
- limites d’intégrale;
- anti-windup conditionnel;
- dérivée filtrée;
- état immutable;
- résultats décomposés P/I/D;
- déterminisme complet.

Le noyau ne revendique ni stabilité universelle ni réglage optimal. Chaque contrôleur réel doit faire l’objet d’une analyse de stabilité, de marges, de robustesse, de limites et de scénarios de faute.

---

## 6. WholeSystemCoSim-T

La co-simulation de démonstration couple :

```text
setpoint
→ sampled software controller
→ PWM quantization
→ drive voltage
→ electrical winding dynamics
→ motor torque
→ rotary-to-linear transmission
→ mass/spring/damper load
→ position sensor + ADC quantization
→ feedback
```

Elle ajoute :

- pertes Joule;
- modèle thermique RC;
- limite de courant;
- limite de température;
- limites de position et vitesse;
- arrêt de sécurité latched;
- délai d’exécution logiciel;
- échéance temps réel;
- biais capteur;
- dérating de tension;
- perte de force moteur;
- tension bloquée;
- perturbation de charge;
- bilan énergétique électrique et mécanique.

### Distinction obligatoire

```text
simulation logicielle ≠ HIL
HIL ≠ banc physique
banc physique ≠ essai terrain
essai terrain ≠ certification
```

---

## 7. PrototypeCompiler-T

Le compilateur transforme une intention en architectures candidates.

### Entrées

- domaines requis;
- type de mouvement;
- puissance continue et de pointe;
- tension d’alimentation;
- volume d’installation;
- charge ou payload;
- priorités de précision;
- efficacité;
- sécurité;
- maintenabilité;
- modularité;
- redondance;
- environnement.

### Familles initiales

1. axe linéaire servo;
2. étage servo rotatif;
3. robot mobile;
4. manipulateur ou pince;
5. skid pompe-vanne;
6. module batterie-convertisseur-thermique;
7. gimbal instrumenté;
8. cellule manufacturière;
9. véhicule autonome intégré;
10. adaptateur de sous-système propulsion.

Le classement est un routage heuristique transparent. Il n’est pas une optimisation physique ni une recommandation d’ingénierie.

---

## 8. FaultPropagation-T

Chaque mode de défaillance contient :

- composant source;
- mode;
- effet local;
- effet système;
- sévérité;
- occurrence ordinale;
- détectabilité ordinale;
- état sûr.

Le moteur suit les connexions orientées et calcule :

- composants atteints;
- domaines atteints;
- profondeur de propagation;
- composants critiques atteints;
- risques de point unique;
- RPN;
- priorité de mitigation.

### Règle OAK

Le RPN est un outil ordinal de priorisation. Il n’est pas une probabilité de défaillance.

---

## 9. RepositoryInventory-T

L’inventaire recherche dans le dépôt les signatures :

- mécaniques;
- rotationnelles;
- électriques;
- électroniques;
- thermiques;
- fluidiques;
- logicielles;
- de données.

Il classe les dossiers en :

```text
physical-only candidate
software-only candidate
cyberphysical candidate
integrated cyberphysical candidate
```

L’inventaire est borné par des budgets de fichiers et d’octets pour chaque exécution, mais n’impose aucun plafond permanent au nombre de systèmes futurs.

### Règle OAK

Une correspondance de mots-clés est une piste de découverte. Elle n’est pas une preuve sémantique. Tout classement canonique exige une revue humaine ou une analyse structurelle plus profonde.

---

## 10. Evidence Ladder D0–D8

```text
D0_STRUCTURE
D1_UNIT_TESTED
D2_SIMULATED_COMPONENT
D3_COSIMULATED_SYSTEM
D4_HIL_SIL
D5_BENCH_EXPERIMENT
D6_FIELD_TRIAL
D7_ENGINEERING_REVIEW
D8_REGULATORY_CERTIFICATION
```

### D0 — Structure

- blueprint;
- composants;
- connexions;
- contrats d’interface.

### D1 — Tests logiciels

- définition des tests;
- environnement;
- nombre exécuté;
- nombre réussi.

### D2 — Simulation composant

- modèles;
- équations;
- paramètres;
- conditions initiales;
- trajectoires finies.

### D3 — Co-simulation système

- contrats d’interface;
- pas d’intégration;
- modèle temporel;
- bilan énergétique;
- stabilité numérique minimale.

### D4 — SIL/HIL

- matériels identifiés;
- hash firmware;
- logs temporels;
- interverrouillages;
- conservation des logs bruts.

### D5 — Banc

- article testé;
- instrumentation;
- calibrations;
- budget d’incertitude;
- hash des données brutes.

### D6 — Terrain

- environnement;
- opérateur;
- supervision;
- journal d’incidents;
- rollback.

### D7 — Revue d’ingénierie

- personne qualifiée;
- discipline;
- portée;
- indépendance;
- artefact signé.

### D8 — Certification

- autorité externe;
- identifiant du certificat;
- portée;
- expiration;
- vérification indépendante.

Le logiciel ne peut jamais produire lui-même une certification D8.

---

## 11. Applications prioritaires

### Mécatronique

- axes CNC;
- robots;
- exosquelettes de recherche non médicaux;
- gimbals;
- convoyeurs;
- mécanismes adaptatifs;
- machines de laboratoire.

### Énergie

- moteurs;
- générateurs;
- batteries;
- convertisseurs;
- micro-réseaux;
- gestion thermique;
- diagnostics BMS.

### Fluides

- pompes;
- valves;
- compresseurs;
- skids;
- refroidissement liquide;
- propulsion;
- hydraulique et pneumatique.

### Instrumentation

- calibrateurs;
- spectromètres motorisés;
- scanners;
- bancs Raman/FTIR;
- positionnement optique;
- systèmes de mesure synchronisés.

### Calcul et électronique

- FPGA;
- microcontrôleurs;
- CPUFMT;
- acquisition;
- contrôle distribué;
- diagnostic de timing;
- capteurs intelligents.

---

## 12. CLI

```bash
omega-cps benchmark
omega-cps blueprint-demo
omega-cps dynamics-demo --model mechanical --summary-only
omega-cps dynamics-demo --model motor --summary-only
omega-cps cosim-demo --summary-only
omega-cps cosim-demo --faulted --summary-only
omega-cps compiler-demo
omega-cps fault-demo
omega-cps evidence-demo
omega-cps inventory --root . --summary-only
```

---

## 13. Statut OAK cible

```text
CERTIFIED_COMPUTATIONAL_CYBER_PHYSICAL_SYSTEMS_R0_1
```

Ce statut signifie seulement :

- contrats typés valides;
- simulations déterministes finies;
- boucle fermée exécutable;
- fautes observables;
- preuves hiérarchisées;
- inventaire reproductible;
- tests logiciels réussis.

Il ne signifie pas :

- sécurité fonctionnelle;
- performance physique réelle;
- robustesse aux conditions non testées;
- compatibilité électromagnétique;
- conformité machine;
- certification automobile, aéronautique, marine, médicale ou industrielle;
- aptitude à construire ou exploiter un matériel réel.

---

## 14. Roadmap

### R0.2 — EnergyGraph et UnitGraph

- conservation énergie/puissance;
- analyse dimensionnelle;
- causalité des ports;
- bilans de pertes;
- passivité.

### R0.3 — HybridAutomata-T

- machines à états hybrides;
- événements;
- transitions de sécurité;
- modes dégradés;
- propriétés temporelles.

### R0.4 — Model Exchange

- import/export FMI/FMU;
- adapters SPICE;
- Modelica;
- ROS 2;
- CAN;
- OPC-UA;
- MQTT;
- logs HIL.

### R0.5 — Digital Twin Evidence

- calibration;
- identification système;
- DiscrepancyTensor;
- incertitudes;
- dérive;
- mise à jour contrôlée des paramètres.

### R0.6 — Prototype Factory

```text
intent
→ blueprint
→ equations
→ simulation
→ control
→ electronics
→ software skeleton
→ tests
→ CAD/PCB requirements
→ BOM candidate
→ FMEA
→ HIL plan
→ bench plan
→ evidence ledger
```

### R1 — System-of-Systems

- flottes;
- usines;
- véhicules multi-modules;
- réseaux énergétiques;
- laboratoires autonomes;
- compagnies physiques-numériques;
- jumeaux de systèmes complets.

---

## 15. Règle canonique

> Un prototype complet n’est pas seulement son code, sa mécanique ou son circuit. C’est un graphe vérifiable de matière, énergie, information, temps, erreurs, preuves et responsabilités.
