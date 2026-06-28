# Ω-DE-TensorProd — EDO/EDP avec TensorProd-Lift

Extension de **Ω-VTP-T++** aux équations différentielles ordinaires et partielles.

## Principe

```text
EDO/EDP non linéaire
→ observables tensoriels
→ opérateur linéaire augmenté
→ troncature
→ résidu OAK
```

Forme canonique :

```text
d/dt Phi_J(Pi_N u) = A_{N,J} Phi_J(Pi_N u) + r_{N,J}
```

où :

- `N` = résolution/projection spatiale pour EDP,
- `J` = degré TensorProd,
- `r_{N,J}` = résidu différentiel + projection + degré + bord + conservation + temps + numérique.

## EDO : Carleman/TensorProd

Pour une EDO polynomiale :

```text
dx/dt = f(x)
```

avec observables :

```text
z_alpha = x^alpha
```

la règle de chaîne donne :

```text
d/dt z_alpha = sum_i alpha_i x^(alpha-e_i) f_i(x)
```

Le module `de_tensorprod.py` construit :

```text
d/dt Phi_J(x) = A_J Phi_J(x) + r_J
```

API :

```python
from omega_vtp_t import PolynomialODE, build_carleman_operator

ode = PolynomialODE(dimension=1, coefficients=({(1,): 0.7, (2,): 0.1},))
op = build_carleman_operator(ode, degree=4)
print(op.closure_coefficient)
print(op.oak_status)
```

## EDP : méthode des lignes

Pour une EDP :

```text
partial_t u = N(u)
```

on discrétise l'espace :

```text
u(x,t) -> vector u(t)
```

puis :

```text
du/dt = F(u)
```

et on applique TensorProd/Koopman/Carleman sur cette grande EDO.

Le module `pde_tensorprod.py` fournit les premiers outils :

- Laplacien 1D périodique,
- gradient 1D périodique,
- réaction-diffusion,
- Burgers visqueux périodique,
- résidu Euler,
- résidu de bord périodique,
- conservation de masse.

API :

```python
from omega_vtp_t import reaction_diffusion_rhs, pde_residual_euler

rhs = reaction_diffusion_rhs(u, dx=dx, diffusion=0.05, reaction=lambda z: z - z**3)
u_next = u + dt * rhs
report = pde_residual_euler(u, u_next, dt=dt, rhs_now=rhs, dx=dx)
print(report.relative_residual)
```

## OAK-safe

Cette extension ne prétend pas résoudre automatiquement toutes les EDP. Elle fournit un cadre vérifiable :

```text
exact en espace infini / tronqué en espace fini / toujours validé par résidu
```

Résidus à séparer :

```text
r_total = r_differential + r_projection + r_degree + r_boundary + r_conservation + r_time + r_numeric
```

## Exemples

```bash
python examples/de_tensorprod_demo.py
python -m unittest discover -s tests
```

## Phrase canonique

```text
Une EDO/EDP non linéaire n'est pas forcément insoluble; elle est souvent linéaire dans un espace d'observables tensoriel plus grand. Mais la vérité est dans le résidu.
```
