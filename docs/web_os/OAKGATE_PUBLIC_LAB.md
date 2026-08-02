# OAKGate Public Lab — Contrat R0.3

## Objet

OAKGate Public Lab aide à examiner si une théorie ou un claim public est suffisamment défini pour passer à une révision humaine, un test ou une comparaison.

Il ne délivre jamais les statuts suivants :

- vrai;
- prouvé;
- scientifiquement validé;
- sécuritaire;
- brevetable;
- conforme;
- prêt à vendre;
- prêt à déployer.

Le statut le plus élevé de R0.3 est :

```text
human-review-candidate
```

## Entrée

L’utilisateur choisit :

- une théorie publique;
- ou un claim public.

Le formulaire est prérempli à partir du catalogue, mais chaque case peut être vérifiée ou corrigée manuellement avant l’évaluation locale.

## Critères

| Critère | Poids | Catégorie | Bloqueur dur |
|---|---:|---|---|
| Portée définie | 0,08 | vérité | non |
| Statut épistémique explicite | 0,08 | vérité | non |
| Support déclaré et traçable | 0,10 | preuve | non |
| Support indépendant disponible | 0,10 | preuve | non |
| Contre-hypothèse explicite | 0,08 | falsification | non |
| Limite ou condition de falsification | 0,10 | falsification | oui |
| Prochain test reproductible | 0,10 | action | oui |
| Baseline de comparaison | 0,08 | test | non |
| Incertitude et domaine de validité | 0,08 | incertitude | non |
| Mémoire négative conservée | 0,06 | apprentissage | non |
| Action suivante réversible | 0,06 | sécurité | non |
| Révision humaine prévue | 0,08 | gouvernance | oui |

La somme des poids est exactement 1.

## Gates

Toutes les portes suivantes doivent être franchies pour supprimer les bloqueurs de publication :

```text
OAKGate
IPGate
PrivacyGate
SecurityGate
```

Une porte franchie dans le formulaire signifie seulement que le paquet déclare cette vérification. Elle ne remplace pas l’expertise humaine correspondante.

## Statuts

### `blocked`

Au moins un bloqueur dur, une gate manquante ou une demande de promotion automatique est présent.

### `insufficiently-specified`

Aucun bloqueur dur n’est présent, mais la complétude pondérée est inférieure à 65 %.

### `draft-testable`

La complétude est comprise entre 65 % et 85 %. L’objet peut être préparé pour un test, sans promotion scientifique.

### `human-review-candidate`

La complétude est d’au moins 85 %, aucune gate n’est manquante et aucun bloqueur dur n’est présent. Une révision humaine reste obligatoire.

## Dette de confiance

La dette de confiance augmente lorsque :

- des critères sont absents;
- une gate est manquante;
- un bloqueur dur existe;
- une promotion automatique est demandée.

Cette valeur est un signal heuristique de préparation, pas une probabilité d’erreur ou de fausseté.

## Promotion automatique

Le moteur retourne toujours :

```json
{
  "automatic_promotion": false
}
```

Même si le formulaire demande une promotion automatique, cette demande devient un bloqueur :

```text
governance.automatic_promotion
```

Le moteur ne peut donc pas s’autoriser lui-même à publier, fusionner, déployer, certifier ou engager Tristan.

## Préremplissage

Le préremplissage utilise des heuristiques prudentes :

- présence d’une formulation et de domaines;
- statut et preuve déclarés;
- support présent;
- distinction entre source interne et support indépendant;
- contre-hypothèses;
- limite;
- prochain test;
- mots indiquant baseline, incertitude ou mémoire négative;
- réversibilité approximative du prochain test;
- garde `automatic_external_action=false`.

Un préremplissage n’est jamais une conclusion. Il sert seulement à réduire la friction de révision.

## Export

Le paquet JSON exporté contient :

- objet audité;
- statut;
- score;
- dette de confiance;
- critères;
- gates;
- bloqueurs;
- critères manquants;
- actions suivantes;
- frontière épistémique;
- horodatage local de génération.

L’export est généré dans le navigateur et n’est transmis à aucun serveur.

## Tests

Les tests JavaScript vérifient :

- somme des poids égale à 1;
- objet vide bloqué;
- objet complet limité au statut `human-review-candidate`;
- promotion automatique convertie en bloqueur;
- absence d’invention de support indépendant;
- maintien du garde-fou de promotion pour les claims.

Commande :

```bash
node --test tests/js/*.test.mjs
```

## Frontière OAK

```text
préparation documentaire ≠ vérité
complétude ≠ validation
hash ≠ preuve
relation ≠ causalité
score ≠ probabilité
candidat à révision ≠ approbation
```
