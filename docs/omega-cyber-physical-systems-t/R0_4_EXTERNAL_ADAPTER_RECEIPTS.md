# Ω-CYBER-PHYSICAL-SYSTEMS-T∞ R0.4

## External Adapter Receipts OS

R0.4 étend Ω-CPS aux outils et réseaux externes utilisés dans les systèmes mécaniques, électriques, électroniques, robotiques, fluidiques, thermiques et logiciels.

## Règle épistémique centrale

```text
dépendance détectée
≠ processus exécuté
≠ modèle convergé
≠ session réseau active
≠ matériel validé
≠ conformité à une norme
≠ certification
```

Chaque niveau doit posséder son propre reçu.

## Familles d’adaptateurs

Le registre initial contient :

1. FMI/FMU;
2. Modelica;
3. SPICE;
4. ROS 2;
5. CAN;
6. OPC-UA;
7. un loopback local de référence pour tester le moteur de reçus.

Le loopback ne simule aucun de ces standards. Il prouve uniquement qu’un processus local réel peut être lancé, limité, audité, haché et rejeté en cas d’erreur.

## CapabilityProbe-T

La sonde recherche des exécutables ou modules candidats :

- `fmpy`;
- `omc` ou `OMPython`;
- `ngspice` ou `xyce`;
- `ros2` ou `rclpy`;
- `candump`, `cansend` ou `python-can`;
- `opcua-client`, `asyncua` ou `opcua`.

Même lorsque ces outils sont trouvés :

```text
integration_active: false
execution_proven: false
hardware_validated: false
standards_compliance_claim: false
```

## ExecutionReceipt-T

Un reçu d’exécution conserve notamment :

- identifiant du connecteur;
- famille d’adaptateur;
- ligne de commande sous forme d’arguments, sans shell;
- timeout;
- code de sortie;
- stdout et stderr;
- contrat JSON de sortie;
- clés manquantes;
- artefacts attendus;
- taille et SHA-256 des artefacts;
- empreinte sémantique stable;
- limites épistémiques.

Le temps d’exécution est enregistré, mais exclu de l’empreinte sémantique afin que deux exécutions déterministes produisent la même preuve malgré la gigue du runner.

## États négatifs conservés

R0.4 distingue :

```text
SUCCESS
NONZERO_EXIT
INVALID_JSON
MISSING_JSON_OUTPUT
MISSING_ARTIFACT
TIMEOUT
EXECUTABLE_NOT_FOUND
```

Une panne attendue dans un test adversarial n’est pas maquillée en intégration réussie.

## NormalizedExchange-T

Des contrats minimaux permettent d’importer ou de rejouer des données sans prétendre qu’une connexion vivante existe :

| Adaptateur | Clés minimales |
|---|---|
| FMI/FMU | `time_s`, `variables` |
| Modelica | `time_s`, `variables` |
| SPICE | `analysis`, `vectors` |
| ROS 2 | `topic`, `message_count` |
| CAN | `channel`, `frames` |
| OPC-UA | `endpoint_id`, `nodes` |
| Loopback | `status`, `samples` |

Sans reçu d’exécution attaché :

```text
replay_only: true
live_connection_claim: false
```

## ActivationGate-T

Un connecteur est actif pour une exécution seulement lorsque :

- le reçu existe;
- l’identifiant correspond;
- le type d’adaptateur correspond;
- le processus a réellement démarré;
- le code de sortie vaut zéro;
- le contrat de sortie est valide;
- tous les artefacts requis existent;
- le reçu déclare le succès pour cette exécution.

La réussite ne se transfère pas automatiquement à un autre connecteur, une autre version, une autre machine ou un autre moment.

## Tests adversariaux

Le benchmark exécute réellement :

- un loopback JSON valide;
- un processus retournant le code 7;
- une sortie non JSON;
- un processus dépassant son timeout;
- un exécutable volontairement absent.

Il teste aussi les six familles externes sous forme de replays déclarés, sans faux matériel ni faux serveur.

## Commandes

```bash
omega-cps-r04 benchmark
omega-cps-r04 capabilities
omega-cps-r04 execute-demo
omega-cps-r04 negative-demo --case nonzero
omega-cps-r04 negative-demo --case invalid-json
omega-cps-r04 negative-demo --case timeout
omega-cps-r04 negative-demo --case missing-executable
omega-cps-r04 normalize-demo --adapter FMI_FMU
omega-cps-r04 normalize-demo --adapter MODELICA
omega-cps-r04 normalize-demo --adapter SPICE
omega-cps-r04 normalize-demo --adapter ROS2
omega-cps-r04 normalize-demo --adapter CAN
omega-cps-r04 normalize-demo --adapter OPCUA
omega-cps-r04 ledger-demo
```

## Statut OAK visé

```text
CERTIFIED_COMPUTATIONAL_EXTERNAL_ADAPTER_RECEIPTS_R0_4
```

Ce statut signifie uniquement que les règles logicielles de découverte, exécution, validation, rejet, normalisation, activation et traçabilité passent sur les fixtures déclarées.

## Revendications interdites

R0.4 laisse toujours faux :

```text
physics_certified
hardware_validated
safety_certified
standards_compliance_claim
live_external_connection_proven
```

Il ne certifie ni FMU, ni modèle Modelica, ni netlist SPICE, ni graphe ROS 2, ni bus CAN, ni serveur OPC-UA, ni machine, ni véhicule, ni installation industrielle.

## Suite falsifiable

R0.5 devra exécuter au moins un outil externe réellement installé dans une matrice CI déclarée, conserver version, modèle d’entrée, paramètres, logs, artefacts, erreurs et reproductibilité. Une intégration ne pourra migrer de `replay_only` à `executed` qu’après ce reçu réel.
