# Ω-ASM-T∞ R1 — Calcul et programmation assembleur optimisés de Tristan

**Statut :** prototype de recherche OAK-safe, autorité `review_only`.  
**Artefact fermé R1 :** IR + analyse statique + backends x86-64/AArch64 + tournoi Pareto + kernel natif x86-64 vérifié différentiellement en CI.

## Principe central

Ω-ASM-T traite l'assembleur comme la couche où se rencontrent :

```text
intention mathématique
-> représentation
-> algorithme
-> graphe de dépendances
-> ASM-IR
-> ISA
-> microarchitecture
-> mesures
-> OAK
```

Le nombre minimal d'instructions n'est pas l'objectif universel. Le coût est multiobjectif :

```text
C(P) = [temps, énergie, taille, trafic mémoire, branches,
        latence, pression registre, pénalités microarchitecturales]
```

R1 matérialise uniquement les axes mesurables sans prétendre résoudre le problème complet.

## ASM-IR

`omega_asm_t.models.Instruction` décrit une opération SSA-like avec :

- opcode;
- sortie unique;
- entrées;
- latence déclarée;
- taille statique;
- octets mémoire;
- probabilité de branche;
- largeur vectorielle;
- métadonnées extensibles.

Les immédiats sont préfixés par `#`. Le validateur rejette les entrées non définies, sorties non SSA, probabilités invalides et coûts négatifs.

## Graphe de dépendances et Dependency Surgery

Pour un programme `P`, R1 construit le DAG de producteurs et calcule le chemin critique :

```text
D(P) = max des sommes de latences sur les chemins producteurs -> sorties
```

Une borne ILP est exposée :

```text
ILP_upper ~= nombre_instructions / chemin_critique
```

Elle est explicitement une métrique structurelle et non une prédiction exacte de l'IPC matériel.

Le fixture `dot_u64_block_program(k)` utilise une réduction en arbre afin d'illustrer la transformation d'une réduction linéaire en profondeur logarithmique.

## Register-Time Volume

Pour chaque valeur SSA `v` :

```text
L(v) = last_use(v) - birth(v)
R_time(P) = somme_v L(v)
```

R1 calcule aussi le pic de valeurs simultanément vivantes. Ces métriques servent de proxy de pression registre avant allocation physique.

## Branch Entropy

Une branche de probabilité `p` reçoit :

```text
H(p) = -p log2(p) - (1-p) log2(1-p)
```

Aucun dogme `branchless = meilleur` n'est adopté. L'entropie décrit seulement l'incertitude informationnelle de la branche; le coût réel dépend du prédicteur et de la microarchitecture.

## ASM-CVCD

R1 produit une signature compacte :

- `F_instruction_count`;
- `D_critical_path`;
- `M_memory_bytes`;
- `R_register_time_volume`;
- `R_peak_live_values`;
- `B_branch_entropy_bits`;
- `V_mean_vector_width`;
- `C_ilp_upper_bound`;
- `I_useful_ops_per_memory_byte`.

Cette signature sert à comparer des représentations. Elle n'est pas une fonction universelle de performance.

## Backends

### x86-64 System V

Deux variantes natives du produit scalaire modulo `2^64` sont fournies :

- `indexed` : adressage base + index*8;
- `ptr` : incrément des pointeurs et décrément du compteur.

### AArch64

Une variante `ptr` utilise des loads post-incrémentés. Elle est actuellement générée et testée statiquement. La CI R1 ne revendique pas d'exécution ARM native.

## Exactitude

R1 utilise `uint64_t`, donc l'addition et la multiplication sont définies modulo `2^64` en C. Les instructions x86-64 utilisent les 64 bits bas du produit, ce qui correspond à cette sémantique.

Niveaux futurs :

- E0 : identité bit-à-bit;
- E1 : entiers avec sémantique définie;
- E2 : flottants sous tolérance déclarée;
- E3 : approximation contrôlée.

Les transformations flottantes ne sont pas incluses dans R1.

## Vérification native

`examples/native/omega_dot_u64_harness.c` compare :

```text
reference_dot
omega_dot_u64_indexed
omega_dot_u64_ptr
```

sur :

- longueur zéro;
- cas scalaire;
- 257 campagnes déterministes;
- longueurs de 0 à 64;
- valeurs 64 bits générées par xorshift déterministe.

Le workflow compile le C et l'assembleur puis exécute le binaire sur le runner x86-64.

Cela prouve uniquement l'équivalence testée de ces fixtures dans ces conditions. Ce n'est pas une preuve formelle exhaustive de tout backend ASM-T.

## Tournoi multiobjectif

Le module `search` expose :

```text
candidats -> vecteurs objectifs -> dominance stricte -> front de Pareto
```

Les scores R1 sont des heuristiques statiques. Toute revendication de vitesse doit provenir d'un benchmark sur la machine cible.

## OAK Court

Chaque rapport garde :

```text
authority = review_only
human_review_required = true
automatic_merge_allowed = false
```

Le système sépare explicitement :

1. structure IR valide;
2. métrique statique;
3. estimation heuristique;
4. vérification différentielle native;
5. benchmark réel;
6. preuve formelle.

Aucun niveau n'est promu automatiquement au suivant.

## CLI

```bash
omega-asm capabilities
omega-asm demo --width 8
omega-asm emit --arch x86_64 --variant ptr
omega-asm tournament --arch x86_64
omega-asm report --width 8
```

## Roadmap fermée -> ouverte

R1 ferme un artefact vérifiable avant expansion. Les prochains candidats, par ordre de valeur :

1. benchmark natif avec cycles, distribution et warmup contrôlé;
2. détection CPU/ISA et manifeste de microarchitecture;
3. modèles de ports/latences versionnés par CPU;
4. register allocator réel;
5. transformations de reassociation prouvées pour entiers;
6. vectorisation AVX2/AVX-512/NEON sous feature gates;
7. génération C/C++/Rust/ASM depuis une même spécification;
8. superoptimisation bornée avec vérificateur SMT;
9. profiling hardware counters lorsque la plateforme le permet;
10. proof-carrying optimization avec certificats rejouables.

## Mémoire négative M−

- moins d'instructions n'implique pas moins de cycles;
- un benchmark unique n'implique pas une amélioration générale;
- une réassociation flottante peut changer le résultat;
- une optimisation x86 ne se généralise pas automatiquement à ARM;
- un estimateur statique n'est pas un compteur matériel;
- un kernel correct sur des fixtures n'est pas une preuve universelle;
- une accélération sans provenance CPU/compilateur/options est non canonique.

## Définition de succès R1

R1 passe OAK lorsque :

```text
package importable
+ CLI fonctionnelle
+ tests Python verts
+ assembly x86-64 assemblable
+ harness différentiel vert
+ CI read-only
+ documentation des limites
+ aucune autorité automatique
```
