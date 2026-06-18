# Protocole OAK — Test empirique Raman / FFWT / CVCD

Statut : **OAK-3 / TESTABLE**.  
Branche : **HGFM scientifique / spectroscopie / compression fertile**.

Ce protocole prépare l'épreuve empirique du théorème de compression fertile : vérifier si un pipeline `LOG -> FFWT -> CVCD -> OAK` extrait des invariants spectraux plus robustes qu'une méthode classique de correction de ligne de base, par exemple ALS.

---

## 1. Hypothèse

Postulat expérimental :

> Sur un spectre Raman bruité avec fluorescence ou ligne de base lente, une transformation HGFM/FFWT/CVCD conserve mieux les pics vibrationnels pertinents qu'une correction classique de ligne de base, à bruit comparable et sans distorsion excessive des positions de pics.

Forme :

```math
X_0 \rightarrow LOG(X_0) \rightarrow FFWT(LOG(X_0)) \rightarrow CVCD \rightarrow \widehat{Y}_{HGFM}
```

À comparer avec :

```math
X_0 \rightarrow ALS(X_0) \rightarrow \widehat{Y}_{ALS}
```

---

## 2. Entrée

Un spectre Raman brut :

```text
x: déplacements Raman, en cm^-1
y_raw: intensité brute = pics + baseline + bruit
```

Cas minimal synthétique :

```math
y_{raw}(x)=\sum_i A_i \exp(-(x-\mu_i)^2 / 2\sigma_i^2)+baseline(x)+noise(x)
```

---

## 3. Transformations comparées

### Baseline classique ALS

Sortie :

```text
y_als_corrected
baseline_als
```

### HGFM / FFWT / CVCD

Sortie attendue :

```text
y_hgfm_invariant
cvcd_components
residue_hgfm
```

Pour v0, CVCD peut être approximé par :

- séparation multi-échelle ;
- rétention des composantes localisées à forte persistance ;
- pénalisation des composantes lentes assimilables à baseline ;
- mesure de stabilité des pics sous bruit bootstrap.

---

## 4. Résidus

Résidus à mesurer :

```math
R_{ALS}=y_{true}-\widehat{y}_{ALS}
```

```math
R_{HGFM}=y_{true}-\widehat{y}_{HGFM}
```

Si le vrai signal est inconnu, utiliser :

- stabilité des positions de pics ;
- stabilité des aires de pics ;
- SNR local ;
- distorsion de largeur ;
- erreur sur un spectre synthétique contrôlé ;
- comparaison à un expert ou à une baseline robuste.

---

## 5. Métriques OAK

| Métrique | Sens |
|---|---|
| `peak_position_error` | erreur moyenne sur positions des pics |
| `peak_area_error` | erreur sur aire/intensité intégrée |
| `snr_gain` | gain signal/bruit |
| `baseline_residual` | baseline restante après correction |
| `distortion_score` | déformation des pics |
| `bootstrap_stability` | robustesse sous bruit |
| `compression_ratio` | réduction sans perte critique |
| `cvcd_fertility` | nombre d'invariants réutilisables |

---

## 6. Critère de passage OAK-4

Le test passe si :

```math
SNR_{HGFM} > SNR_{ALS}
```

et :

```math
Distortion_{HGFM} \le Distortion_{ALS}+\epsilon
```

et :

```math
PeakError_{HGFM} \le PeakError_{ALS}
```

sur au moins un spectre synthétique contrôlé ou un dataset réel avec référence.

---

## 7. Verdicts possibles

| Résultat | Verdict |
|---|---|
| HGFM bat ALS sur SNR et pics | OAK-4 partiel |
| HGFM égale ALS mais produit invariants interprétables | OAK-3/4 fertile |
| HGFM améliore SNR mais déforme les pics | M_MINUS partiel / ajuster pénalité |
| HGFM perd contre ALS | M_MINUS utile / revoir CVCD |
| résultat non reproductible | UNKNOWN |

---

## 8. Pseudocode v0

```python
x, y_raw, y_true = generate_or_load_raman_spectrum()

# Baseline classique
y_als = als_baseline_correction(y_raw)

# Pipeline HGFM approximatif
y_log = log_compress_spectrum(y_raw)
coeffs = ffwt_or_wavelet_decompose(y_log)
components = cvcd_select_persistent_components(coeffs)
y_hgfm = reconstruct_from_components(components)

metrics = compare_methods(
    y_true=y_true,
    y_raw=y_raw,
    y_als=y_als,
    y_hgfm=y_hgfm,
    x=x,
)

oak_report = oak_decide(metrics)
```

---

## 9. Résidu expérimental

Manques actuels :

- implémentation FFWT réelle ;
- définition opérationnelle stricte de CVCD spectral ;
- dataset Raman réel ;
- comparaison à plusieurs baselines ;
- incertitude statistique ;
- protocole de reproduction.

---

## 10. Prochaine action minimale

Créer un script :

```text
experiments/raman_cvcd/test_synthetic_raman_cvcd.py
```

qui génère un spectre synthétique, applique ALS et un premier extracteur CVCD approximatif, puis écrit un rapport OAK JSON.
