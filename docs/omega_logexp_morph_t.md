# Ω-LOGEXP-MORPH-T∞

## Calcul logarithmique des transformations et morphismes de Tristan

**Version R0.1 — prototype OAK-safe**

## 0. Statut

Ce module transforme l'intuition

\[
T \stackrel{?}{=} \exp(L_T)
\]

en une architecture testable.

La formulation directe n'est pas universelle :

- une exponentielle matricielle est toujours inversible;
- un morphisme peut être rectangulaire;
- une réflexion réelle n'est pas une exponentielle réelle unique;
- un logarithme matriciel est multivalué;
- une représentation exponentielle exacte peut ne fournir aucune compression.

La formulation opérationnelle retenue est

\[
T
=
\pi_{\mathrm{out}}
\mathcal D_{\tau(T)}
\overleftarrow{\prod}_{j=1}^{m}
\exp(\Gamma_j)
\iota_{\mathrm{in}}
+
R_T.
\]

Elle sépare :

1. le relèvement \(\iota_{\mathrm{in}}\);
2. le secteur discret \(\tau(T)\);
3. les générateurs continus \(\Gamma_j\);
4. la projection \(\pi_{\mathrm{out}}\);
5. le résidu \(R_T\).

## 1. Vocabulaire

Le mot **noyau** reste réservé à

\[
\ker T=\{x:T(x)=0\}.
\]

Le module emploie :

- \(N_T\) : représentation normalisée de la transformation;
- \(L_T=\Log_\beta(N_T)\) : logarithme associé à une branche \(\beta\);
- \(\Gamma_T\) : génome générateur compressé;
- \(R_T\) : résidu de reconstruction;
- \(\tau(T)\) : secteur discret ou topologique.

## 2. Exponentielle directe

Pour un endomorphisme suffisamment régulier,

\[
N_T=e^{L_T}.
\]

Le prototype fournit une exponentielle de matrices réelles finies par mise à
l'échelle, série de Taylor et élévations au carré.

Cette routine est conçue pour les petits noyaux scientifiques et les tests,
pas pour remplacer une bibliothèque d'algèbre linéaire numérique industrielle.

## 3. Logarithme local gardé

Le logarithme actuel utilise la série de Mercator :

\[
\Log(I+X)
=
X-\frac{X^2}{2}+\frac{X^3}{3}-\cdots
\]

avec la condition explicite

\[
\|X\|_\infty<1.
\]

Donc

\[
L_T=\Log(N_T)
\]

n'est calculé que si

\[
\|N_T-I\|_\infty<1.
\]

À l'extérieur de cette zone, le programme échoue explicitement au lieu de
choisir silencieusement une branche instable ou complexe.

## 4. Relèvement nilpotent universel des applications linéaires

Pour

\[
T:\mathbb R^n\rightarrow\mathbb R^m,
\]

on définit

\[
\mathcal N_T=
\begin{pmatrix}
0&0\\
T&0
\end{pmatrix}.
\]

Alors

\[
\mathcal N_T^2=0
\]

et

\[
e^{\mathcal N_T}=I+\mathcal N_T.
\]

Pour une entrée relevée

\[
\iota(x)=
\begin{pmatrix}
x\\0
\end{pmatrix},
\]

on obtient

\[
e^{\mathcal N_T}\iota(x)
=
\begin{pmatrix}
x\\Tx
\end{pmatrix}.
\]

Cette représentation reste exacte pour les transformations :

- singulières;
- rectangulaires;
- non injectives;
- non surjectives.

Elle prouve la représentabilité exponentielle relevée, mais pas la compression.

## 5. Composition non commutative

Pour deux générateurs \(A\) et \(B\),

\[
e^Ae^B=e^{\operatorname{BCH}(A,B)}.
\]

Le prototype implémente BCH jusqu'au degré quatre :

\[
\operatorname{BCH}(A,B)
=
A+B
+\frac12[A,B]
+\frac1{12}[A,[A,B]]
+\frac1{12}[B,[B,A]]
-\frac1{24}[B,[A,[A,B]]].
\]

Le commutateur

\[
[A,B]=AB-BA
\]

mesure l'effet de l'ordre des transformations.

Dans une interprétation physique, un commutateur n'est un couplage réel que
si les générateurs, variables, unités et équations ont été validés.

## 6. Secteurs discrets

Le prototype rapporte :

- forme de la matrice;
- rang;
- signe du déterminant si la matrice est carrée;
- inversibilité.

Comme

\[
\det(e^A)=e^{\operatorname{tr}A}>0,
\]

une réflexion réelle doit être séparée du générateur continu.

Une future version représentera explicitement :

\[
N_T=\mathcal D_{\tau(T)}e^{L_T}.
\]

## 7. Compression dans une base de générateurs

Une bibliothèque finie est donnée :

\[
\mathcal G=\{G_1,\ldots,G_p\}.
\]

On cherche

\[
\Gamma_T
=
\sum_{j=1}^{p}\theta_jG_j.
\]

Le prototype effectue une projection de moindres carrés avec une faible
régularisation de crête.

Il retourne :

- les coefficients \(\theta_j\);
- le générateur reconstruit;
- le résidu logarithmique relatif.

La compression est fertile seulement si

\[
\operatorname{DL}(\Gamma_T)
+
\operatorname{DL}(R_T)
<
\operatorname{DL}(N_T)
\]

et si la représentation généralise hors des données d'ajustement.

## 8. Défaut de semi-groupe

Pour une dynamique autonome,

\[
N_{t+s}=N_tN_s.
\]

Le module mesure

\[
\Delta_{\mathrm{SG}}
=
\frac{\|N_{t+s}-N_tN_s\|_F}
{\|N_{t+s}\|_F}.
\]

Un défaut non nul peut signaler :

- une variable cachée;
- une mémoire;
- une dépendance temporelle;
- une erreur expérimentale;
- une représentation insuffisante;
- un changement de régime.

Il ne prouve pas à lui seul lequel de ces mécanismes est responsable.

## 9. Couplage avec Ω-QUATERNION-CRYSTAL-T

Pour un cristal,

\[
F=RU,
\]

avec

\[
R=e^\Omega,
\qquad
U=e^E.
\]

Donc

\[
F=e^\Omega e^E
\]

et localement

\[
\Log F=\operatorname{BCH}(\Omega,E).
\]

Les contributions peuvent être organisées comme :

- \(\Omega\) : rotation cristalline;
- \(E\) : étirement logarithmique;
- \([\Omega,E]\) : effet d'ordre rotation-déformation;
- termes supérieurs : histoire non commutative.

Les quaternions continuent d'encoder l'orientation, tandis que les matrices et
tenseurs conservent les déformations, stress, propriétés constitutives et
couplages physiques.

## 10. API minimale

```python
from omega_logexp_morph_t import (
    bch,
    compress_in_basis,
    matrix,
    matrix_exponential,
    matrix_logarithm_near_identity,
    nilpotent_lift,
)
```

### Exponentielle

```python
generator = matrix([[0.0, 0.1], [-0.1, 0.0]])
transformation = matrix_exponential(generator)
```

### Logarithme local

```python
recovered = matrix_logarithm_near_identity(transformation)
```

### Relèvement

```python
linear_map = matrix([[1.0, 2.0, 0.0], [0.0, 0.0, 1.0]])
lifted_generator = nilpotent_lift(linear_map)
```

### CLI

```bash
omega-logexp-morph \
  --generator '[[0,0.1],[-0.1,0]]'
```

ou

```bash
omega-logexp-morph \
  --transformation '[[1,0.1],[0,1]]'
```

## 11. OAKBench

Les tests vérifient :

1. \(e^0=I\);
2. reconstruction log-exp locale;
3. rejet hors du domaine de Mercator;
4. relèvement exact d'un morphisme rectangulaire;
5. avantage de BCH sur \(A+B\) pour deux générateurs non commutatifs;
6. propriété de semi-groupe d'un générateur autonome;
7. récupération de coefficients dans une base;
8. détection des secteurs réflexion/singularité;
9. représentation affine homogène;
10. positivité du déterminant d'une exponentielle réelle.

## 12. Limites

Le prototype ne fournit pas encore :

- logarithme matriciel global;
- spectre complexe;
- formes de Jordan;
- choix automatique de branche;
- algorithme de Schur réel;
- dérivée de Fréchet du logarithme;
- identification à partir de séries temporelles bruitées;
- Koopman ou DMD;
- bases de Lie apprises;
- contraintes physiques automatiques;
- longueur de description calculée;
- validation expérimentale.

## 13. Prochaine trajectoire

### R0.2

- logarithme réel 2x2/3x3 spécialisé;
- registre de branches;
- générateurs \(\mathfrak{so}(3)\), \(\mathfrak{se}(3)\), déformation et affine;
- intégration quaternion-cristal;
- rapports JSON OAK.

### R0.3

- Magnus pour générateurs dépendant du temps;
- graphes de commutateurs;
- détection de défaut de semi-groupe dans les données;
- estimation parcimonieuse des générateurs.

### R0.4

- FFWT multi-échelle des champs de générateurs;
- EBSD, Raman, stress, température et phase;
- comparaison aux baselines DMD, Koopman et identification de systèmes.

## 14. Règle canonique

\[
\boxed{
\text{Exponentiable}
\neq
\text{compressible}
\neq
\text{physiquement expliqué}.
}
\]

Une revendication ne passe OAK que si elle fournit :

- représentation;
- branche;
- domaine;
- résidu;
- incertitude;
- invariants;
- baseline;
- validation hors échantillon.
