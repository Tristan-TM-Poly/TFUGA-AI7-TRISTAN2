# Ω-SYNERGY-N-T∞ R2 — Architecture

## Flux principal

```text
measurements / CreationDNA / PR records
  -> normalized subset lattice
  -> exact Möbius decomposition
  -> uncertainty and necessity
  -> sparse interaction tensor
  -> order spectrum
  -> Synergy Complex
  -> OAK gate
  -> factorial or adaptive experiment
  -> proof ledger and deterministic bundle
```

## Modules

| Module | Responsabilité |
|---|---|
| `models` | contrats typés et niveaux N0–N10 |
| `combinatorics` | treillis booléen et masques |
| `mobius` | décomposition exacte et reconstruction |
| `factorial` | plans complets, fractionnaires, contrastes, alias |
| `spectrum` | énergie, densité, pureté et dette par ordre |
| `hypergraph` | hyperarêtes et fermeture simpliciale |
| `minimality` | ablations et noyaux minimaux |
| `search` | exhaustif, beam, branch-and-bound |
| `experiment` | compilation et arrêt adaptatif |
| `information` | mesures multivariées et XOR |
| `tensor` | tenseur symétrique clairsemé |
| `bayes` | mise à jour normale prudente |
| `uncertainty` | demi-vie et comparaison contextuelle |
| `pr_hypergraph` | constellations, vagues et hyper-épistasie |
| `oak` | gates non compensatoires |
| `ledger` | chaîne append-only |
| `reporting` | bundle SHA-256/Merkle |
| `adapters` | CreationDNA vers signatures de recherche |
| `cli` | surface d'exécution stable |

## Complexité

- transformée exacte : `O(3^n)` dans l'implémentation lisible actuelle lorsqu'elle somme les sous-ensembles pour chaque coalition;
- nombre de mesures complètes : `2^n`;
- espace des coalitions d'ordre `k` : `C(m,k)`;
- beam search : borné par `beam_width × m × max_order` après déduplication;
- stockage tensoriel : proportionnel aux interactions matérialisées.

Une transformée rapide de Möbius `O(n 2^n)` est une extension R2.1 naturelle pour les univers proches de la limite exacte.

## Déterminisme

- composants triés et dédupliqués;
- identifiants SHA-256;
- exploration pseudo-aléatoire dérivée du hash des coalitions;
- sérialisation JSON triée;
- `SOURCE_DATE_EPOCH` pour les bundles CI;
- actions GitHub épinglées par SHA.

## Compatibilité

R2 est un package séparé `omega_synergy_n_t`.
Il consomme les sorties `creation_dna.json` de `omega_synergy_t` via un adaptateur conservateur.
Il ne remplace ni la Foundry R1 ni Synergy OS R0.2 : il constitue leur cour mathématique d'interactions supérieures.

## Extension rules

Toute extension doit :

1. préserver la distinction mesure/interprétation;
2. déclarer la convention mathématique;
3. ajouter une fixture négative;
4. conserver provenance et contexte;
5. ne jamais promouvoir une autorité par score;
6. documenter complexité et hypothèses;
7. garder rollback et bornes finies.
