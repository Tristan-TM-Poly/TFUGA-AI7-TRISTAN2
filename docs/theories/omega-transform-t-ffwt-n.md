# Ω-TRANSFORM-T — Transformées de Tristan / FWT / FFWT / FFWT-N

Statut : **prototype OAK-safe**. Cette branche formalise les transformées comme opérateurs LOG/EXP qui déplacent un objet brut vers un espace compressé où émergent des invariants CVCD, des résidus OAK et des prototypes testables.

## Définition mère

```text
X brut -> LOG/Transformée -> coefficients C -> CVCD -> invariants I -> EXP/reconstruction -> X_hat -> OAK -> résidu R
```

Forme canonique :

```text
T_T(X) = C
X = T_T^{-1}(C) + R
R = X - X_hat
```

Une bonne transformée maximise la compression, la stabilité et l'utilité prédictive, tout en minimisant l'erreur, le coût et les résidus non expliqués.

## FWT-T

La FWT-T est le socle rapide en ondelettes. Elle sépare un signal en approximation lente et détails multi-échelles.

```text
FWT-T(X) = {a_J, d_J, d_{J-1}, ..., d_1}
```

Interprétation :

- `a_J` : tronc compressé;
- `d_j` : branches/résidus à l'échelle j;
- reconstruction exacte si tous les coefficients Haar sont conservés;
- baseline obligatoire pour toute extension FFWT.

## FFWT-T

La FFWT-T ajoute une couche de fertilité fractale à la FWT.

```text
FFWT-T(X) = FWT(X) + poids fractaux + invariants CVCD + rapport OAK
```

Coefficient pondéré :

```text
C_tilde[j,k] = F[j,k] * C[j,k]
```

Poids heuristique MVP :

```text
F[j,k] = 1 + amplitude + persistence + roughness
```

OAK important : les poids sont actuellement heuristiques. Ils doivent battre les baselines sur des tâches mesurables avant d'être canonisés comme supérieurs.

## FFWT-N-T

Le N signifie simultanément :

1. N dimensions : signaux, images, volumes, champs;
2. N variables : cohérence entre canaux ou capteurs;
3. N niveaux : transformées récursives sur les coefficients;
4. N nœuds : hypergraphe de coefficients;
5. N non-linéarités : résidus et anomalies multi-échelles.

Forme récursive :

```text
X_0 = X
X_{n+1} = FFWT(X_n)
```

La FFWT-N est donc une transformée de transformées : motifs, motifs de motifs, grammaire de motifs, puis méta-invariants.

## Hypergraphe des coefficients

Chaque coefficient peut devenir un nœud :

```text
v = (scale j, position k, channel c, wavelet lambda, algebra a)
```

Les hyperarêtes relient les coefficients par persistance, phase, cohérence, causalité, résidu ou utilité. Le CVCD extrait ensuite les invariants stables de cet hypergraphe.

## Mémoire négative M⁻ initiale

Premier OAKBench local :

- reconstruction FWT Haar exacte : erreur relative ~9.3e-16;
- à `keep_fraction = 0.2`, la FWT simple bat la FFWT heuristique sur un signal synthétique en erreur de reconstruction;
- conclusion : la pondération fractale naïve est fertile mais non supérieure en reconstruction sparse brute.

Cette M⁻ est volontaire : la FFWT doit maintenant être optimisée et testée surtout sur l'anomalie, le débruitage, la classification, la stabilité et la cohérence multi-échelle.

## Règle OAK

```text
Pas de révolution sans benchmark.
```

Toute version plus ultra doit produire :

- erreur de reconstruction;
- ratio de compression;
- stabilité sous bruit;
- performance tâche;
- comparaison FWT/FFT/SVD/DCT/STFT/CWT;
- résidus M⁺/M⁻.

## Prochaine cible

Faire évoluer ce MVP vers :

- ondelettes Daubechies/Symlets;
- FFWT 2D/3D/ND;
- fractalgram/scalogram;
- OAKBench spectroscopie/cristaux;
- OAKBench RLC/résonance;
- détection d'anomalies multi-échelles;
- sélection automatique de transformée universelle Ω-UTT.
