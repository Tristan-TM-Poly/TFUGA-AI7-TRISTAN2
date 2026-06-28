# Ω-VTP-T++ TensorProd-Lift Prototype

Prototype GitHub pour la branche **Ω-VTP-T++ — TensorProd-Lift de Tristan**.

## Ce que ça fait

- Génère les multi-index \(\alpha\)
- Construit le lift monomial \(\Phi_J(v)=\{v^\alpha:|\alpha|\le J\}\)
- Construit la version directe \(\prod_i(1+v_i)^{j_i}\)
- Évalue des polynômes comme produits linéaires dans l'espace augmenté
- Ajuste un opérateur linéaire \(z_{t+1}\approx A z_t\)
- Produit des rapports OAK minimaux : résidu, conditionnement, rang, features

## Exemple

```python
from omega_vtp_t import polynomial_eval_from_lift

v = [[2.0, 3.0]]
coeffs = {
    (0, 0): 2.0,
    (2, 0): 3.0,
    (1, 1): 5.0,
    (0, 3): -7.0,
}

print(polynomial_eval_from_lift(v, 3, coeffs))
```

## Tests

```bash
python -m unittest discover -s tests
python examples/tensorprod_demo.py
```

## Règle OAK

Pas de linéarisation déclarée sans résidu mesuré.
