# Ω-RIGID-BODY-T R0.1 — Corps rigide triaxial libre

## Statut OAK

Ce module formalise et calcule le problème classique de la toupie d'Euler sans couple externe pour trois moments principaux distincts

\[
0<I_1<I_2<I_3.
\]

Le noyau fournit des identités analytiques exactes et des vérifications numériques reproductibles. Il ne revendique aucune nouvelle loi physique, aucune validation expérimentale et aucune certification de système mécanique réel.

## Équations d'Euler

Dans le repère propre du corps,

\[
I_1\dot\omega_1=(I_2-I_3)\omega_2\omega_3,
\quad
I_2\dot\omega_2=(I_3-I_1)\omega_3\omega_1,
\quad
I_3\dot\omega_3=(I_1-I_2)\omega_1\omega_2.
\]

Les invariants sont

\[
E=\frac12\sum_i I_i\omega_i^2,
\qquad
L^2=\sum_i I_i^2\omega_i^2.
\]

À moment cinétique fixé,

\[
\frac{L^2}{2I_3}\le E\le\frac{L^2}{2I_1}.
\]

## Branche stable autour de l'axe 3

Pour

\[
\frac{L^2}{2I_3}<E<\frac{L^2}{2I_2},
\]

\[
\omega_1=A\,\operatorname{cn}(u|m),\quad
\omega_2=B\,\operatorname{sn}(u|m),\quad
\omega_3=C\,\operatorname{dn}(u|m),\quad u=\Omega_3t+u_0,
\]

avec

\[
A^2=\frac{2EI_3-L^2}{I_1(I_3-I_1)},\quad
B^2=\frac{2EI_3-L^2}{I_2(I_3-I_2)},\quad
C^2=\frac{L^2-2EI_1}{I_3(I_3-I_1)},
\]

\[
\Omega_3^2=\frac{(I_3-I_2)(L^2-2EI_1)}{I_1I_2I_3},
\qquad
m=\frac{(I_2-I_1)(2EI_3-L^2)}{(I_3-I_2)(L^2-2EI_1)}.
\]

## Branche stable autour de l'axe 1

Pour

\[
\frac{L^2}{2I_2}<E<\frac{L^2}{2I_1},
\]

\[
\omega_1=A\,\operatorname{dn}(u|m),\quad
\omega_2=B\,\operatorname{sn}(u|m),\quad
\omega_3=C\,\operatorname{cn}(u|m),\quad u=\Omega_1t+u_0,
\]

avec

\[
B^2=\frac{L^2-2EI_1}{I_2(I_2-I_1)},
\]

et les mêmes expressions pour \(A\) et \(C\), tandis que

\[
\Omega_1^2=\frac{(I_2-I_1)(2EI_3-L^2)}{I_1I_2I_3},
\qquad
m=\frac{(I_3-I_2)(L^2-2EI_1)}{(I_2-I_1)(2EI_3-L^2)}.
\]

La période de la polhodie est

\[
T_{\rm pol}=\frac{4K(m)}{\Omega}.
\]

## Séparatrice et retournement de l'axe intermédiaire

À

\[
E=\frac{L^2}{2I_2},
\]

le paramètre elliptique tend vers \(m=1\), donc

\[
\operatorname{sn}(u|1)=\tanh u,
\qquad
\operatorname{cn}(u|1)=\operatorname{dn}(u|1)=\operatorname{sech}u.
\]

La solution canonique devient

\[
\omega_1=A_s\operatorname{sech}(\lambda t),\quad
\omega_2=\frac{L}{I_2}\tanh(\lambda t),\quad
\omega_3=C_s\operatorname{sech}(\lambda t),
\]

\[
\lambda^2=\frac{L^2(I_3-I_2)(I_2-I_1)}{I_1I_2^2I_3}.
\]

C'est la structure analytique du retournement de la raquette de tennis. La période diverge logarithmiquement parce que \(K(m)\to\infty\) lorsque \(m\to1^-\).

## « Rotation de la rotation »

Le vecteur moment cinétique \(\mathbf L\) est fixe dans le repère inertiel, mais ses composantes et celles de \(\boldsymbol\omega\) parcourent une courbe fermée dans le repère du corps. Pour un choix ZXZ dont l'axe inertiel \(z\) est aligné sur \(\mathbf L\),

\[
\cos\theta=\frac{I_3\omega_3}{L},
\qquad
\psi=\operatorname{atan2}(I_1\omega_1,I_2\omega_2),
\]

\[
\dot\phi=
L\frac{I_1\omega_1^2+I_2\omega_2^2}
{I_1^2\omega_1^2+I_2^2\omega_2^2}.
\]

L'intégration de \(\phi\) est une intégrale elliptique de troisième espèce. Après une période de polhodie, l'orientation accumule une phase dynamique et une phase géométrique :

\[
\Delta\Gamma=\frac{2ET_{\rm pol}}{L}-\mathcal A\pmod{2\pi},
\]

où \(\mathcal A\) est l'angle solide orienté enfermé par la trajectoire de \(\mathbf L/L\) sur la sphère du corps. Le noyau reconstruit également l'orientation par quaternion à partir de la vitesse angulaire analytique.

## Utilisation

```bash
omega-rigid-body benchmark
omega-rigid-body analyze-state --inertia 1 2 3 --omega 0.9 0.2 0.8
omega-rigid-body sample --inertia 1 2 3 --energy 1.8 --angular-momentum 3 --duration 8 --count 129
omega-rigid-body separatrix --inertia 1 2 3 --angular-momentum 3 --duration 10 --count 129
python examples/omega_rigid_body_demo.py
pytest -q tests/test_omega_rigid_body_t.py
```

## Limites R0.1

- couple externe nul seulement pour les branches analytiques;
- moments propres strictement distincts et ordonnés;
- branche elliptique canonique réelle, les changements de signes et déphasages représentant les autres points de la même courbe;
- reconstruction quaternionique numérique, tandis que la phase Euler complète est documentée comme quadrature elliptique;
- aucun frottement, corps déformable, sloshing interne ou couplage translation-rotation;
- aucune donnée expérimentale.

Les extensions naturelles sont : couples faibles par variation lente de \((E,L,m,u_0)\), rotation-déformation, corps gyrostatique, Hamiltonien/Lax pair, phase de Montgomery numérique, et comparaison à des mesures IMU.
