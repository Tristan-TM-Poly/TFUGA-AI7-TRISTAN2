# Ω-VTP-T++ v2 — OAK / Koopman / CVCD

Cette extension transforme le prototype TensorProd-Lift en laboratoire de linéarisation non linéaire vérifiable.

## Nouveaux modules

| Module | Rôle |
|---|---|
| `bases.py` | bases stabilisées, dont Chebyshev tensoriel |
| `conditioning.py` | conditionnement, résidus, score OAK |
| `closure_residual.py` | mesure si `Phi(y)` appartient au span de `Phi(x)` |
| `koopman_tensorprod.py` | fit de l'opérateur `g(y) ≈ K g(x)` |
| `train_test_oak.py` | généralisation train/test et gap OAK |
| `cvcd_selector.py` | scoring de fertilité et sélection CVCD des features |

## Fermeture tensorielle

Le lift n'est utile que si l'espace est presque fermé sous la dynamique :

```text
Phi(x_{t+1}) ≈ A Phi(x_t)
```

Le rapport de fermeture mesure :

```text
closure_coefficient = 1 - relative_residual
```

Règle OAK : un grand espace de features ne suffit pas; il doit être fermé, stable, et pas trop coûteux.

## Koopman-Tristan

On ajuste un opérateur linéaire dans l'espace des observables :

```python
from omega_vtp_t import fit_koopman_tensorprod

fit = fit_koopman_tensorprod(x, y, degree=3, lift="monomial")
print(fit.fit.report.relative_residual)
print(fit.closure.closure_coefficient)
```

## Bases stabilisées

Les monômes bruts peuvent être mal conditionnés. La v2 ajoute Chebyshev :

```python
from omega_vtp_t import chebyshev_lift

lift = chebyshev_lift(x, degree=4, domain=([-1.0], [1.0]))
```

Chebyshev est utile sur domaines bornés parce que les bases sont mieux contrôlées que `1, x, x^2, ...`.

## CVCD fertility

Chaque feature reçoit un score :

```text
score = normalized_variance + target_correlation - memory_penalty * degree
```

Puis on garde les features fertiles :

```python
from omega_vtp_t import tensor_prod_lift, select_cvcd_features

lift = tensor_prod_lift(samples, degree=2)
selection = select_cvcd_features(lift, target, top_k=4)
```

Ce n'est pas encore une preuve causale; c'est une sélection expérimentale OAK-compatible.

## Train/test OAK

La v2 pénalise l'overfit :

```python
from omega_vtp_t import train_test_koopman_oak

report = train_test_koopman_oak(x, y, degree=3, lift="monomial")
print(report.test_relative_residual)
print(report.score.oak_status)
```

## Commandes

```bash
python -m unittest discover -s tests
python examples/tensorprod_v2_demo.py
```

## Phrase canonique v2

```text
Toute non-linéarité polynomiale est une projection d'une dynamique linéaire dans un espace d'observables tensoriel; la vérité de cette linéarisation se mesure par fermeture, résidu, stabilité, généralisation et coût.
```
