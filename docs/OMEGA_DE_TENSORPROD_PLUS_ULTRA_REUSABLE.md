# Ω-DE-TensorProd∞ — Plus Ultra Reusable Layer

Cette couche transforme Ω-DE-TensorProd en architecture plus réutilisable : résidus nommés, invariants, sélection adaptative, compression low-rank, solveur lifté et mémoire négative M⁻.

## Nouveaux modules

| Module | Rôle |
|---|---|
| `residual_decomposition.py` | composants de résidu nommés, tolérances, agrégation OAK |
| `invariant_guards.py` | conservation, positivité, énergie L2, invariants personnalisés |
| `adaptive_de.py` | sélection automatique du degré TensorProd pour EDO polynomiale |
| `low_rank_operator.py` | compression SVD d'opérateurs liftés |
| `lifted_solvers.py` | solveurs Euler/RK4 pour systèmes linéaires liftés |
| `mminus_registry.py` | registre M⁻ des lifts/features/opérateurs dangereux ou coûteux |
| `auxiliary_variables.py` | templates de variables auxiliaires pour polynomialisation |

## Résidus nommés

Au lieu d'un seul scalaire :

```text
residual = 1.2e-4
```

on utilise :

```text
degree_residual
boundary_residual
conservation_residual
time_residual
compression_residual
numeric_residual
```

API :

```python
from omega_vtp_t import ResidualComponent, decompose_residuals

report = decompose_residuals([
    ResidualComponent("degree", 1e-4, 1e-3),
    ResidualComponent("boundary", 1e-12, 1e-8),
])
print(report.oak_status)
print(report.worst_component)
```

## Invariant guards

Les invariants sont des gardiens OAK :

```python
from omega_vtp_t import conservation_check, positivity_check, invariant_report

report = invariant_report([
    conservation_check("mass", before_mass, after_mass, tolerance=1e-8),
    positivity_check(u_next, tolerance=0.0),
])
```

Règle : un modèle qui prédit bien mais viole les invariants physiques doit être surveillé ou rejeté.

## Sélection adaptative du degré

```python
from omega_vtp_t import PolynomialODE, select_ode_tensor_degree

ode = PolynomialODE(dimension=1, coefficients=({(1,): 0.7, (2,): 0.1},))
selection = select_ode_tensor_degree(ode, samples, min_degree=1, max_degree=5)
print(selection.best_degree)
```

Principe : ne pas choisir le plus grand degré; choisir le meilleur compromis résidu/coût.

## Compression low-rank

```python
from omega_vtp_t import build_carleman_operator, compress_operator_svd

op = build_carleman_operator(ode, degree=4)
compressed = compress_operator_svd(op.operator, energy_tol=0.999)
```

OAK mesure :

```text
relative_error
compression_ratio
rank
oak_status
```

## Solveur lifté

```python
from omega_vtp_t import solve_lifted_linear

trajectory, report = solve_lifted_linear(z0, A, dt=0.01, steps=100, method="rk4")
```

But : expérimenter rapidement avec :

```text
dz/dt = A z
```

sans ajouter SciPy.

## Mémoire négative M⁻

```python
from omega_vtp_t import entry_from_oak_status, build_mminus_registry

entry = entry_from_oak_status(
    "degree_2_logistic",
    "experimental_truncation_residual_high",
    evidence="degree=2 leaves x^3 terms",
)
registry = build_mminus_registry([entry])
```

M⁻ transforme les échecs en connaissances réutilisables.

## Variables auxiliaires

Certaines fonctions non polynomiales peuvent devenir polynomialement traitables par augmentation :

```text
s = sin(x), c = cos(x)
y = exp(x)
q = 1/x
```

API :

```python
from omega_vtp_t import standard_auxiliary_templates

for template in standard_auxiliary_templates("x"):
    print(template.name, template.derivative_rules)
```

## Phrase canonique

```text
Ω-DE-TensorProd∞ ne promet pas de résoudre magiquement toutes les dynamiques; il promet une architecture où chaque lift, chaque compression, chaque solveur et chaque approximation laissent un résidu mesurable, un invariant vérifiable et une mémoire négative réutilisable.
```

## Démo

```bash
python examples/plus_ultra_reusable_demo.py
python -m unittest discover -s tests
```
