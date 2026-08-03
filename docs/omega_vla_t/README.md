# Ω-VLA-T∞ R0.1

## Calcul vectoriel et algèbre linéaire de Tristan

Ω-VLA-T∞ est le noyau géométrique et opératoriel reliant espaces, métriques,
transformations, champs, flux, graphes, hypergraphes, compression CVCD et
validation OAK.

## Statut épistémique

R0.1 implémente uniquement des objets établis de mathématiques numériques :

- espaces vectoriels réels de dimension finie avec métrique définie positive;
- applications linéaires et adjoints métriques;
- résidus, noyaux numériques, SVD, rang exact estimé et rang effectif;
- changements de base et test de covariance;
- gradient, divergence, Laplacien et rotationnel 2D par différences finies;
- gradient, divergence et Laplacien sur graphe via matrice d’incidence;
- décomposition de Hodge de premier ordre d’un flot d’arêtes;
- rapports OAK déterministes et explicitement bornés.

Les interprétations HGFM, CVCD, Noether-Tristan, FFWT et sédénioniques restent
des architectures de recherche tant que leurs opérateurs, hypothèses,
invariants et domaines de validité ne sont pas formalisés et comparés aux
méthodes établies.

## Principe canonique

```text
objet -> espace -> métrique -> base -> opérateur -> spectre
      -> variation -> invariant -> compression -> résidu -> OAK
```

Un vecteur représente un état orienté dans un espace de possibilités. Une
matrice représente les coordonnées d’un opérateur, pas l’opérateur abstrait.
Une dérivée est d’abord un covecteur; la métrique la transforme en gradient.
Une approximation n’est acceptable que si son résidu est conservé et mesuré.

## API minimale

```python
import numpy as np
from omega_vla_t import LinearOperator, VectorSpace, audit_operator

space = VectorSpace(2, metric=np.array([[2.0, 0.0], [0.0, 1.0]]))
operator = LinearOperator(
    np.array([[2.0, 1.0], [0.0, 3.0]]),
    space,
    space,
    name="A",
)

print(operator.svd_report().to_dict())
print(audit_operator(operator).to_markdown())
```

## CLI

```bash
omega-vla benchmark --output generated/omega_vla_t/benchmark.json
omega-vla audit '[[2,1],[0,3]]' --name A --markdown
```

## OAKBench

R0.1 vérifie notamment :

1. la linéarité numérique;
2. la covariance sous changement de base pour les endomorphismes;
3. la finitude et le seuil du conditionnement;
4. la cohérence du rang numérique;
5. la symétrie et la semi-définie positivité du Laplacien de graphe;
6. la reconstruction et l’orthogonalité de la décomposition de Hodge;
7. l’absence explicite de revendication de théorème ou de validation physique.

Un passage OAK signifie seulement que les fixtures logicielles déclarées ont
réussi. Il ne constitue ni preuve mathématique nouvelle, ni certification
physique, ni validation expérimentale.

## Frontières R0.2+

- formes différentielles et complexes de chaînes d’ordres supérieurs;
- calcul extérieur discret sur complexes simpliciaux;
- Hodge pondéré et multi-échelle HGFM;
- Jacobien, Hessien et propagation d’incertitude;
- atlas de linéarisations locales Ω-LIN-T;
- projections fertiles CVCD comparées à PCA/SVD/wavelets;
- tenseurs CP, Tucker et Tensor Train;
- unités physiques et covariance dimensionnelle;
- bancs d’essai Raman, cristaux, Maxwell, fluides et systèmes dynamiques.

## Règle anti-flou

```text
théorie non testée = hypothèse
architecture non codée = architecture
code non testé = brouillon
fixture testée = actif logiciel borné
preuve formelle ou démonstration = théorème, seulement après vérification
```
