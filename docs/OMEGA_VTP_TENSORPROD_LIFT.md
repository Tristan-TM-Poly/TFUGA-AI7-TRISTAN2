# Ω-VTP-T++ — TensorProd-Lift de Tristan

## Noyau

\[
\Phi_J(v)
=
\bigotimes_{i=1}^{n}
\left[
\bigoplus_{j=0}^{J}
(1+v_i)^{\circ j}
\right]
\]

Interprétation opérationnelle :

```text
non-linéaire dans v  ->  linéaire dans Phi_J(v)
```

Le module implémente deux bases :

1. `tensor_prod_lift`: base monomiale propre  
   \[
   \Phi_J(v)=\{v^\alpha:\alpha\in\mathbb{N}^n,\ |\alpha|\le J\}
   \]

2. `one_plus_lift`: base proche de la notation Tristan  
   \[
   \Psi_J(v)=\{\prod_i(1+v_i)^{j_i}\}
   \]

## Théorème OAK-safe

Toute non-linéarité polynomiale entière de degré borné \(J\) peut être écrite
comme une fonction linéaire dans l'espace augmenté :

\[
F(v)=w^\top \Phi_J(v)
\]

si :

\[
F(v)=\sum_{|\alpha|\le J} c_\alpha v^\alpha
\]

Pour une dynamique :

\[
x_{t+1}=F(x_t)
\]

on cherche :

\[
\Phi_J(x_{t+1})=A_J\Phi_J(x_t)+r_J
\]

Le résidu \(r_J\) est obligatoire : pas de linéarisation déclarée sans résidu.

## Limites

| Cas | Statut |
|---|---|
| Polynôme degré \(\le J\) | exact |
| Polynôme degré \(>J\) | tronqué |
| Fonction analytique | série/troncature avec résidu |
| Fonction non analytique | base adaptée ou approximation |
| Discontinuité | non garantie |
| Chaos | local/lifté possible, résidu critique |

## Explosion dimensionnelle

Nombre de monômes jusqu'au degré \(J\) en dimension \(n\) :

\[
N = \binom{n+J}{J}
\]

Donc la version complète doit être suivie de CVCD/OAK :

```text
Full TensorProd -> Sparse/Block/Hierarchical/Fractal TensorProd -> OAK residual
```

## API minimale

```python
from omega_vtp_t import tensor_prod_lift, polynomial_eval_from_lift

v = [[2.0, 3.0]]
phi = tensor_prod_lift(v, degree=3)

coeffs = {
    (0, 0): 2.0,
    (2, 0): 3.0,
    (1, 1): 5.0,
    (0, 3): -7.0,
}

print(polynomial_eval_from_lift(v, 3, coeffs))
```

## OAKBench

```python
from omega_vtp_t.oakbench_vtp import (
    oak_polynomial_exactness_demo,
    oak_dynamic_lift_demo,
    oak_speed_memory_demo,
)

print(oak_polynomial_exactness_demo())
print(oak_dynamic_lift_demo(degree=4))
print(oak_speed_memory_demo())
```

## Statut canonique

Cette branche appartient à :

```text
Ω-VTP-T / Vectorisation, Tensorisation et Parallélisme de Tristan
Ω-LIN-T / Linéarisation des systèmes non-linéaires de Tristan
Ω-CVCD-T / Compression fertile et sélection d'invariants
OAK / validation, falsification, résidu mesuré
```

Phrase canonique :

```text
Toute non-linéarité entière est une linéarité cachée dans un espace tensoriel plus grand.
```

Phrase OAK-safe :

```text
Toute non-linéarité polynomiale entière de degré borné est exactement linéarisable
par TensorProd complet; toute autre non-linéarité exige expansion, approximation
ou résidu mesuré.
```
