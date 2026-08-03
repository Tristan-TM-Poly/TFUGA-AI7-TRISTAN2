# Ω-ZETA-MANDEL-T — Zêta-Mandelbrot-Tristan

## Statut OAK

Cette branche est un laboratoire numérique et théorique. Elle ne constitue pas une preuve de l'hypothèse de Riemann, ni une nouvelle loi mathématique certifiée. Toute visualisation, symétrie apparente ou stabilité d'orbite doit être traitée comme un signal exploratoire jusqu'à preuve analytique indépendante.

Phrase de garde:

> On ne prouve pas Riemann avec une image; on construit un microscope OAK pour explorer les structures qui pourraient inspirer une preuve.

## Idée centrale

Ω-ZETA-MANDEL-T relie:

- les fonctions zêta et L;
- les zéros, pôles, produits d'Euler et nombres premiers;
- les ensembles de Mandelbrot et Julia;
- les dynamiques holomorphes et les bassins de Newton;
- les algèbres de Cayley-Dickson: R, C, H, O, sédénions;
- les diviseurs de zéro, défauts de commutativité/associativité et projections robustes;
- HGFM, CVCD, OAK, U² et mémoire négative M⁻.

Forme mère:

```math
\Omega_{\zeta M T}
=
\operatorname{OAK}_{U^2}
\left(
\operatorname{CVCD}
\left[
\operatorname{HGFM}
(
\zeta,
L,
p_n,
\rho_k,
M,
J,
\mathbb S,
Z_{\text{div}},
\operatorname{Orbit}
)
\right]
\right)
```

## Familles canoniques

### 1. Mandelbrot-CVCD

```math
z_{n+1}=z_n^2+c,\quad z_0=0
```

Sortie: temps d'échappement, rayon maximal, signature symbolique, proxy de Lyapunov, compressibilité d'orbite, incertitude U².

### 2. Julia-CVCD

```math
z_{n+1}=z_n^2+c
```

avec `z0` variable. Sert à comparer espace des paramètres et espace des conditions initiales.

### 3. Zeta-Orbit Set

```math
s_{n+1}=\zeta(s_n)+c
```

ou dynamique de Newton:

```math
s_{n+1}=s_n-\alpha\frac{\zeta(s_n)}{\zeta'(s_n)}
```

But: cartographier des bassins numériques autour des zéros connus, sans surinterprétation.

### 4. Mandelbrot-Zêta

```math
z_{n+1}=z_n^2+c,\quad y_n=\zeta(z_n)
```

On classe les paramètres `c` selon la stabilité/compressibilité de `zeta(z_n)`.

### 5. Prime-Perturbed Mandelbrot

```math
z_{n+1}=z_n^2+c+\epsilon p_n^{-s}
```

Les nombres premiers deviennent un bruit arithmétique structuré à comparer contre des baselines aléatoires.

### 6. L-Function Fractal Lab

```math
s_{n+1}=L(s_n,\chi)+c
```

Permet de comparer les empreintes fractales de différentes fonctions L.

### 7. Sedenion-Mandelbrot

```math
Z_{n+1}=Z_n^2+C,\quad Z,C\in\mathbb S
```

Tout résultat dépend de la norme, projection, précision, seuil d'échappement et parenthésage.

### 8. Zero-Divisor Fractals

On mesure un risque d'annihilation:

```math
Z_{\text{risk}}(X)
=
\min_{Y\neq0}
\frac{\|XY\|}{\|X\|\|Y\|}
```

Plus le score est proche de 0, plus le comportement pseudo-stable peut venir d'une annihilation algébrique.

### 9. Critical-Line Dynamics

Étude de dynamiques près de:

```math
s=\frac12+it
```

OAK strict: cohérence autour de la droite critique n'est pas une preuve.

### 10. Noether-CVCD Fractal Residues

Pour une transformation `G`:

```math
R_G=\operatorname{CVCD}(X)-\operatorname{CVCD}(GX)
```

`R_G` mesure la brisure de symétrie dynamique.

## Invariants CVCD minimaux

- `escape_iter`
- `max_radius`
- `final_radius`
- `mean_radius`
- `radius_variance`
- `lyapunov_proxy`
- `compressed_signature`
- `uncertainty_u2`
- `commutativity_defect`
- `associativity_defect`
- `zero_divisor_risk`
- `symmetry_residue`

Le prototype actuel implémente le noyau minimal; les invariants hyperalgébriques complets sont prévus dans les prochaines phases.

## Règles OAK obligatoires

1. Déclarer algèbre, norme, projection, seuil et précision.
2. Déclarer le parenthésage pour toute algèbre non associative.
3. Comparer aux baselines classiques avant toute extension sédénionique.
4. Tester stabilité sous résolution, projection, norme, précision et seuil d'échappement.
5. Enregistrer les motifs invalidés dans M⁻.
6. Ne jamais élever une visualisation au statut de preuve.
7. Toute affirmation sur Riemann doit rester `heuristique` sauf preuve analytique formelle.

## Roadmap

### Phase 0 — baseline

- Mandelbrot classique reproductible.
- CVCD minimal.
- Tests unitaires.

### Phase 1 — zêta

- Zeta-orbit set.
- Bassins de Newton de zêta.
- Comparaison `eta-series` vs moteur haute précision externe.

### Phase 2 — Mandelbrot-Zêta

- Échantillonnage `zeta(z_n)`.
- Cartes de phase/module.
- Mémoire négative des artefacts de pole, troncature et résolution.

### Phase 3 — Cayley-Dickson

- Quaternions/octonions/sédénions.
- Parenthesis audit.
- Zero-divisor atlas.

### Phase 4 — OAKBench

- Rapports JSON reproductibles.
- Tests multi-précision.
- Tests multi-projection.
- Baselines aléatoires pour prime perturbation.

### Phase 5 — Conjecture miner

- Extraction automatique de motifs persistants.
- Classement Bayes-Tristan: vérité/utilité/fertilité/testabilité.
- Statuts: visualization, heuristic, conjecture, numerical evidence, theorem.
