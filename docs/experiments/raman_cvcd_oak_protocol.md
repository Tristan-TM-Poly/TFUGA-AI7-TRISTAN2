# Protocole OAK — Test empirique Raman / FFWT / CVCD

Statut : **OAK-3 / TESTABLE + seed exécutable synthétique**.  
Branche : **HGFM scientifique / spectroscopie / compression fertile**.

Ce protocole prépare l'épreuve empirique du théorème de compression fertile : vérifier si un pipeline `LOG -> FFWT -> CVCD -> OAK` extrait des invariants spectraux plus robustes qu'une méthode classique de correction de ligne de base, par exemple ALS.

Un premier seed exécutable existe maintenant :

```text
experiments/raman_cvcd/synthetic_raman_cvcd.py
```

Il génère un spectre Raman synthétique, ajoute baseline et bruit, compare une baseline lisse classique à un extracteur CVCD-like multi-échelle, puis émet un rapport OAK JSON. Ce seed ne valide pas encore l'hypothèse Raman réelle : il sert de friction calculable minimale.

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

## 8. Seed exécutable v0

```bash
python experiments/raman_cvcd/synthetic_raman_cvcd.py
```

Sortie : rapport OAK JSON contenant :

- `status` ;
- `verdict` ;
- métriques baseline ;
- métriques HGFM/CVCD-like ;
- résidus expérimentaux.

---

## 9. Résidu expérimental

Manques actuels :

- implémentation FFWT réelle ;
- définition opérationnelle stricte de CVCD spectral ;
- dataset Raman réel ;
- comparaison à plusieurs baselines dont ALS réel ;
- incertitude statistique ;
- protocole de reproduction plus large.

---

## 10. Prochaine action minimale

Remplacer le proxy baseline par un vrai ALS et ajouter une suite de tests statistiques sur plusieurs graines synthétiques.
