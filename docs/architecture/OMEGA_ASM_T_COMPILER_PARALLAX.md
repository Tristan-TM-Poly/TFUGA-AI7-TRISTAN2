# Ω-ASM-T∞ — Compiler Parallax C / C++ / Rust / ASM

## Mission

Compiler Parallax compare plusieurs matérialisations du **même contrat sémantique** sans transformer un benchmark ponctuel en classement universel de langages.

Contrat R2 initial :

```text
dot_u64_mod_2^64(a,b,n) = sum_i a[i]*b[i] mod 2^64
```

Implémentations :

```text
C
C++
Rust no_std / wrapping arithmetic
x86-64 ASM indexed
x86-64 ASM pointer
```

## Isolation du compilateur

Chaque langage est compilé dans une unité de traduction distincte, sans LTO. Le harness C voit seulement des déclarations `extern` et des pointeurs de fonctions.

Cela évite le défaut P4-v1 où le compilateur pouvait optimiser le corps de la référence C différemment des fonctions ASM opaques.

```text
source C   -> C.o   --┐
source C++ -> C++.o --┤
source Rust-> Rust.o--┤-> harness externe -> correctness + P4
ASM source -> ASM.o --┘
```

## P3 differential court

Avant toute mesure, les cinq symboles sont comparés à une référence `uint64_t` sur 257 campagnes déterministes et des longueurs variant de 0 à 256.

Toute divergence stoppe le tribunal de performance.

## P4-v2 parallax benchmark

Le benchmark utilise :

- 4096 éléments;
- 31 rounds;
- 127 répétitions par échantillon;
- ordre de départ tournant entre cinq variantes;
- barrière mémoire opaque autour de chaque appel;
- symboles externes compilés séparément;
- checksum dépendant de l'itération;
- aucun seuil de vitesse en CI.

Le raw JSON porte :

```text
benchmark_protocol_version = 2
parallax = true
separate_translation_units = true
anti_hoist_memory_barrier = true
```

`omega-asm benchmark-report` produit ensuite les distributions robustes et ratios médians relatifs à `reference_c`.

## Artifact ledger

Chaque implémentation possède :

```text
implementation_id
language
symbol
source SHA-256
object SHA-256
object size
disassembly SHA-256
toolchain identity
flags
```

Le désassemblage est extrait **par symbole** avec `objdump` afin que les variantes ASM partagent éventuellement un même objet tout en gardant des preuves textuelles distinctes.

CLI :

```bash
omega-asm parallax-report descriptor.json --output parallax.json
```

Le package ne lance ni compilateur ni `objdump`; il valide et hash uniquement les artefacts produits par la cour contrôlée.

## Interprétation

Une différence de code machine peut être fertile :

- vectorisation différente;
- déroulage;
- adressage;
- réduction;
- allocation de registres;
- branchement;
- scheduling.

Mais :

```text
disassembly différent != sémantique différente
disassembly différent != performance meilleure
un run rapide != langage supérieur
```

Compiler Parallax est donc un **générateur d'hypothèses microarchitecturales**, connecté ensuite à P4/P5/P6 et éventuellement P7.

## OAK

- `authority = review_only`;
- correction différentielle avant timing;
- LTO interdit dans ce tribunal;
- source/object/disassembly hashes obligatoires;
- package n'exécute pas les compilateurs;
- aucune autorité automatique;
- aucune conclusion globale C vs C++ vs Rust vs ASM.

## Extensions

1. Clang vs GCC parallax pour C/C++;
2. plusieurs `rustc -C target-cpu/target-feature`;
3. `-O0/-O1/-O2/-O3/-Os` atlas;
4. AVX2/AVX-512 feature gates;
5. AArch64/NEON native court;
6. P5 counters par implémentation isolée;
7. P6 replication par exact binary hash;
8. P7 translation validation pour fenêtres machine sélectionnées.
