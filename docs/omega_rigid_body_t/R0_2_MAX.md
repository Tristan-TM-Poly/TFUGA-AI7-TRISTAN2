# Ω‑RIGID‑BODY‑T R0.2 MAX

## Statut

R0.2 MAX est un laboratoire analytique et computationnel sans dépendance scientifique externe pour le corps rigide triaxial. Il prolonge R0.1 sans remplacer les résultats classiques de la mécanique rationnelle.

**Certifié par OAKBench :** identités analytiques codées et fixtures numériques déterministes.

**Non certifié :** expérience physique, IMU, satellite, véhicule, contrôleur de vol, sûreté, qualification industrielle ou nouvelle loi de la physique.

## 1. Problème

Pour des moments principaux ordonnés

\[
0<I_1<I_2<I_3,
\]

les équations d'Euler dans le repère du corps sont

\[
\begin{aligned}
I_1\dot\omega_1&=(I_2-I_3)\omega_2\omega_3+\tau_1,\\
I_2\dot\omega_2&=(I_3-I_1)\omega_3\omega_1+\tau_2,\\
I_3\dot\omega_3&=(I_1-I_2)\omega_1\omega_2+\tau_3.
\end{aligned}
\]

Sans couple,

\[
E=\frac12\sum_i I_i\omega_i^2,
\qquad
L^2=\sum_i I_i^2\omega_i^2
\]

sont invariants. R0.2 traite quatre couches : solution elliptique exacte, orientation quaternionique, géométrie de Poinsot/phase de Montgomery et perturbations vérifiables.

## 2. Récupération exacte depuis un état initial arbitraire

R0.2 récupère automatiquement la phase et le secteur de signes pour tout état initial réel non séparatrix. Les transformations admissibles satisfont

\[
s_1s_2s_3=+1.
\]

Les quatre secteurs sont explorés, puis la phase elliptique est estimée par recherche déterministe grille + section dorée. `ExactParameters` contient le régime, les amplitudes, la fréquence, le paramètre \(m=k^2\), la période, la phase, la signature et le résidu de reconstruction.

```bash
omega-rigid-body-r02 fit \
  --i1 1 --i2 2 --i3 3 \
  --omega -0.2 -0.3 1.0
```

## 3. Rotation de la rotation : phase de Montgomery

Après une période de polhodie, la vitesse angulaire dans le corps revient à son état initial, mais l'orientation complète accumule une rotation autour du moment cinétique inertiel fixe :

\[
\Delta\Gamma
=
\underbrace{\frac{2ET}{L}}_{\text{phase dynamique}}
-
\underbrace{\Omega_{\mathbb S^2}}_{\text{angle solide orienté}}
\pmod{2\pi}.
\]

R0.2 calcule l'angle solide de la trajectoire de \(\mathbf L/L\) sur la sphère et compare la phase prédite à la monodromie quaternionique obtenue par intégration indépendante.

```bash
omega-rigid-body-r02 phase \
  --i1 1 --i2 2 --i3 3 \
  --omega 0.2 0.3 1.0 \
  --samples 4096
```

La sortie contient phase dynamique, angle solide, phase de Montgomery, phase quaternionique, résidu modulo \(2\pi\), erreur d'axe et erreur de fermeture.

## 4. Intégrateur conservatif

Le point milieu implicite est appliqué au système sans couple :

\[
\omega_{n+1}=\omega_n+h f\!\left(\frac{\omega_n+\omega_{n+1}}2\right).
\]

Pour des invariants quadratiques, ce schéma les préserve à la précision de la résolution non linéaire. R0.2 utilise Newton avec jacobienne analytique \(3\times3\).

```bash
omega-rigid-body-r02 midpoint \
  --i1 1 --i2 2 --i3 3 \
  --omega 0.2 0.3 1.0 \
  --t-end 100 --steps 20000
```

## 5. Couples, amortissement et orientation

R0.2 intègre conjointement \((\boldsymbol\omega,q,W,\mathbf J)\) avec Dormand–Prince 5(4) adaptatif. Le couple effectif est

\[
\boldsymbol\tau_{\rm eff}=\boldsymbol\tau_{\rm ext}-c\boldsymbol\omega.
\]

Les bilans vérifiés sont

\[
E(t)-E(0)=\int_0^t\boldsymbol\tau\cdot\boldsymbol\omega\,dt,
\]

\[
\mathbf L_I(t)-\mathbf L_I(0)=\int_0^tR(q)\boldsymbol\tau\,dt.
\]

```bash
omega-rigid-body-r02 simulate \
  --i1 1 --i2 2 --i3 3 \
  --omega 0.4 -0.2 0.8 \
  --t-end 12 --samples 240 \
  --constant-torque 0.003 -0.002 0.004 \
  --damping 0.01
```

## 6. Stabilité des axes principaux

Pour une rotation de vitesse \(\Omega_0\),

\[
\nu_1=|\Omega_0|\sqrt{\frac{(I_2-I_1)(I_3-I_1)}{I_2I_3}},
\]

\[
\lambda_2=|\Omega_0|\sqrt{\frac{(I_2-I_1)(I_3-I_2)}{I_1I_3}},
\]

\[
\nu_3=|\Omega_0|\sqrt{\frac{(I_3-I_1)(I_3-I_2)}{I_1I_2}}.
\]

Les axes 1 et 3 sont stables; l'axe intermédiaire 2 est instable.

## 7. Poinsot, polhodie et herpolhodie

Le module expose `polhode_points`, `momentum_sphere_path`, `herpolhode_points` et `oriented_solid_angle_closed_polygon`. Ces objets relient visualisation, invariants et phase géométrique sans confondre courbe numérique et preuve.

## 8. Carte stroboscopique

Pour un couple périodique, `poincare` échantillonne l'état une fois par période :

```bash
omega-rigid-body-r02 poincare \
  --i1 1 --i2 2 --i3 3 \
  --omega 0.2 0.3 1.0 \
  --forcing-period 0.5 --cycles 200 \
  --torque-amplitude 0.001 0.0005 0.0002 \
  --damping 0.002
```

C'est une infrastructure d'étude de bifurcations et de chaos, pas une preuve automatique de chaos.

## 9. Atlas inertie–énergie

`atlas` balaie les rapports d'inertie et fractions d'énergie. Chaque cellule contient régime, paramètre elliptique, période, taux de stabilité, identifiant déterministe et SHA‑256 du manifeste.

```bash
omega-rigid-body-r02 atlas \
  --inertia-count 16 \
  --energy-count 128 \
  --output generated/omega_rigid_body_t/r02/atlas.json
```

La taille du balayage est un choix fini d'expérience, pas une limite permanente.

## 10. OAKBench R0.2

Le banc vérifie :

1. récupération phase/signes dans les deux régimes;
2. conservation longue durée du point milieu;
3. angle solide d'un triangle sphérique connu;
4. phase de Montgomery contre monodromie quaternionique;
5. alignement de l'axe de monodromie;
6. bilan énergie–travail sous couple et amortissement;
7. bilan moment–impulsion inertiel;
8. théorème stable–instable–stable;
9. déterminisme cryptographique de l'atlas.

```bash
omega-rigid-body-r02 benchmark
pytest -q tests/test_omega_rigid_body_r02.py
```

## 11. Limites et R0.3

R0.2 ne couvre pas les corps déformables, le ballottement, les impacts, l'identification expérimentale, l'estimation IMU, la commande de vol ni la qualification industrielle.

Directions R0.3 : intégrateur de Moser–Veselov sur \(SO(3)\), variables d'Andoyer–Deprit, perturbation multi-échelle des paramètres elliptiques, continuation de bifurcations, identification Bayes‑Tristan, figures reproductibles et comparaison C/C++/Rust/Python.
