# Ω-MAIL-T R0.2 — Atlas CVCD matérialisé

Ce répertoire matérialise 49 152 cellules synthétiques sous une représentation positionnelle et révisable par Git.

## Structure

```text
scenario/cXX/iYY.cells  -> 64 scénarios anomalie × langue
routing/cXX/iYY.cells   -> 64 benchmarks de routage correspondants
oak/cXX/iYY.cells       -> 64 benchmarks OAK correspondants
```

Chaque fichier contient exactement les 64 cellules `a00|l0` à `a15|l3`. Le chemin fournit la compagnie, l'intention et la couche; la ligne fournit l'anomalie et la langue. L'identité canonique est donc :

```text
<layer>/<company>/<intent>/<anomaly>/<locale>
```

## Cardinalité

```text
16 compagnies × 16 intentions × 16 anomalies × 4 langues = 16 384 scénarios
16 384 scénarios × 1 benchmark de routage = 16 384 benchmarks de routage
16 384 scénarios × 1 benchmark OAK = 16 384 benchmarks OAK
TOTAL = 49 152 enregistrements matérialisés
```

## Pourquoi la structure partage les mêmes blobs

Git permet à plusieurs chemins de référencer le même contenu immuable. Ici, la sémantique non répétitive est portée par le chemin, tandis que la grille anomalie-langue est commune. Cette déduplication conserve 49 152 enregistrements adressables et 768 fichiers visibles tout en évitant de stocker 768 copies physiques inutiles du même bloc.

## Frontière OAK

Toutes les identités sont synthétiques, tous les domaines applicatifs sont `.test`, la livraison externe est désactivée et les cellules ne constituent ni consentement, ni message envoyé, ni incident réel, ni validation empirique, ni certification de sécurité.
