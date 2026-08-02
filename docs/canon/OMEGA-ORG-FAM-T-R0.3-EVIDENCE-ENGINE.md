# Ω-ORG-FAM-T R0.3 — Evidence Engine

## Statut

R0.3 transforme l'atlas de familles de R0.2 en moteur de preuves révisables. Il ne prétend pas identifier une molécule à partir d'un pic, d'un SMARTS, d'une formule ou d'un score unique.

## Noyau livré

1. parseur de formules moléculaires avec parenthèses et isotopes explicites;
2. équilibrage stœchiométrique exact par algèbre rationnelle;
3. objets de provenance immuables avec qualité de source;
4. règles spectrales numériques par plages, tolérances et contre-signatures;
5. fusion multimodale conservant contradictions et statut OAK;
6. déconvolution non négative de mélanges sans dépendance externe;
7. registre SMARTS/SMIRKS versionné et empreinté;
8. exécution RDKit optionnelle, jamais supposée disponible;
9. ledger SHA-256 append-only avec chaîne de hachage;
10. index SQLite des bundles, sources, observations et scores;
11. benchmark synthétique massif avec abstention, bruit, signaux manquants et contre-signatures.

## Front massif R0.3

Le premier OAKBench matérialise **8 388 608 scénarios** déterministes dans 16 shards binaires gzip. Chaque cas encode famille attendue, décision, confiance et facteurs de difficulté.

Résultats de référence locaux :

- précision hors abstention : 0,643157;
- couverture : 0,803862;
- abstentions : 1 645 324;
- racine Merkle : `f504713bff192b1afcda3f8ba0a94796348ae4ff0d05aae7666f77edf282aec3`;
- temps observé : environ 22,5 s;
- mémoire maximale observée : environ 116 MiB.

Ces métriques décrivent une baseline synthétique volontairement difficile. Elles ne mesurent aucune performance sur des molécules ou spectres expérimentaux.

## OAK

```text
formule équilibrée != réaction réalisable
SMARTS compatible != structure identifiée
bande compatible != molécule identifiée
fit de mélange != composition certifiée
source présente != source fiable
score élevé != preuve indépendante
benchmark synthétique != validation expérimentale
```

La promotion d'une identification exige au minimum provenance, conditions, incertitudes, alternatives, contre-signatures, convergence de modalités indépendantes et comparaison à une référence appropriée.

## Commandes

```bash
omega-organic-evidence parse-formula C6H4(OH)2
omega-organic-evidence balance --reactants C2H6 O2 --products CO2 H2O
omega-organic-evidence benchmark --cases 8388608 --clean
omega-organic-evidence audit-benchmark generated/omega_org_fam_t_r03_evidence_benchmark
```

## Frontière suivante

R0.4 doit remplacer progressivement les règles semées par des entrées ouvertes ou autorisées, versionnées par source et conditions : spectres réels, incertitudes instrumentales, structures de référence, réactions atomiquement mappées et jeux de validation séparés de l'entraînement.
