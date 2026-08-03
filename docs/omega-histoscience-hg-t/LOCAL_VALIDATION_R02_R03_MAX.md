# Ω-HISTOSCI-HG-T∞ — Reçu local R0.2–R0.3 MAX

Date de validation : **2026-08-03**  
Environnement : **Python 3.13.5**  
Portée : R0.2 et R0.3 MAX uniquement; les 20 tests R0.1 avaient déjà été validés avant leur fusion, mais n'ont pas été réexécutés dans ce workspace réduit.

## Résultat exécutable

```text
90 passed in 14.37s
R0.2 : 52 tests
R0.3 : 38 tests
```

Statuts OAK obtenus :

```text
CERTIFIED_SOFTWARE_HISTORIOGRAPHIC_FRONTIER_R0_2
CERTIFIED_SOFTWARE_HISTORIOGRAPHIC_STREAMING_FRONTIER_R0_3
```

## R0.2 matérialisé

```text
32 racines scientifiques
16 dimensions épistémiques
16 opérateurs historiques
8 classes d'évidence
32 modes M−
8 192 cellules de branches
65 536 cellules de recherche
73 728 cellules totales
274 877 906 944 coordonnées logiques étendues
```

Les données sont réparties en :

- 8 shards de branches × 1 024 lignes;
- 16 shards de recherche × 4 096 lignes;
- un manifeste de matérialisation;
- des reçus OAK et de couverture.

Racines Merkle :

```text
branches : d1a8fd2fba49e46f24e8742c20d1a66e0dd3aa9ff6f3348778378d918f952b92
recherche: 4a485d607b1c43d11566555ca941afbd97366f22aaec3d2f4b88dda5df3d2166
```

## R0.3 MAX exécuté

```text
frontière canonique : 524 288
frontière étendue  : 274 877 906 944
coordonnées streamées réellement : 100 000
modes M− : 32
```

Le stream est paresseux : il ne charge pas la frontière complète en mémoire et conserve rang, dérang, checkpoint et provenance logicielle.

## Payloads et correction M−

Hashes canoniques :

```text
R0.2: 11367099b3a3cfb4e26be6d713af4ef4faa9ccca29c91b4c95109202754223fa
R0.3: 2f7c7fc677c7ea643b04ba0853c6715b34e0be88df00c85c85a32eab81ae61f9
```

Une anomalie historique a été détectée dans la provenance R0.2 : `part_008.txt` contient exactement `part_010.txt` comme suffixe dupliqué. Le matérialisateur corrigé ne retire ce suffixe que si cette condition exacte est observée, puis exige le hash canonique R0.2. Toute autre divergence échoue immédiatement.

## Artefact déterministe

```text
chemin : artifacts/omega-histoscience-r02-r03-max-materialized.tar.gz
SHA-256: 4d1a9ae79d33b27a7c24ef429dd302f68899fc711609163edb1d36fac849dae9
taille : 404 679 octets
fichiers: 85
lignes texte représentées: 80 002
```

Composition :

- 34 entrées de templates R0.2;
- 24 entrées de templates R0.3;
- 53 fichiers sources distincts après coalescence des chemins partagés;
- 32 fichiers matérialisés R0.2;
- schémas, tests, exemples, workflows et documentation.

Vérification :

```bash
python tools/install_omega_histosci_max_artifact.py --check-only
```

Extraction sûre dans un répertoire vide :

```bash
python tools/install_omega_histosci_max_artifact.py \
  --extract-to /tmp/omega-histoscience-max
```

L'installateur refuse les chemins absolus, `..`, liens symboliques, liens physiques, mauvais hash, mauvaise taille, mauvais nombre de fichiers et écrasements non explicitement autorisés.

## Frontières épistémiques

```text
SOFTWARE_FIXTURE != HISTORICAL_TRUTH
GENERATED_CELL != VERIFIED_HISTORICAL_EVENT
SUCCESSION != DOCUMENTED_INFLUENCE
NUMERICAL_SCORE != HISTORIOGRAPHIC_PROOF
LARGE_FRONTIER != GLOBAL_EXHAUSTIVENESS
TRANSLATION_ROUNDTRIP != SEMANTIC_EQUIVALENCE
```

```text
historical_truth_certified: false
source_completeness_claimed: false
global_exhaustiveness_claimed: false
decolonial_completeness_claimed: false
software_validation_only: true
permanent_total_cap: null
```

## État GitHub Actions

Les runs MAX observés sont restés `queued` sans attribution de runner et sans première étape. Il ne s'agit donc pas d'un échec de test Histoscience. Le présent reçu et l'artefact adressé rendent la validation reproductible indépendamment de cette file.
