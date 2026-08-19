# HGFM TensorBench R0.1

## Question falsifiable

Sur un tenseur synthétique gouverné de forme `16×16×16`, un générateur de
candidats conscient des hyperarêtes retrouve-t-il l’optimum exact avec moins de
20 % des évaluations exhaustives?

Le benchmark ne teste pas une supériorité universelle de HGFM. Il teste une
propriété plus étroite : la valeur de relations d’ordre trois préenregistrées
pour une recherche structurée.

## Tenseur

```text
T = (K16 ⊗ O16 ⊗ D16) ⊙ A_OAK ⊙ E
```

- `K16`: seize noyaux de l’écosystème;
- `O16`: seize opérateurs;
- `D16`: seize domaines;
- `A_OAK`: masque d’admissibilité;
- `E`: force probante synthétique.

Les `4096` coordonnées sont toutes calculables. La recherche exhaustive donne
l’optimum de référence et le front de Pareto exact.

## Baselines

1. recherche exhaustive;
2. échantillonnage aléatoire à cinq graines;
3. montée de coordonnées gloutonne;
4. recherche HGFM structurée.

## Ablations

- `without_ffwt`: retire la cohérence multi-échelle synthétique;
- `without_hgfm`: retire les relations d’ordre trois;
- `without_cvcd`: retire la pénalité de dette et duplication;
- `without_oak`: retire la quarantaine du score.

Ces noms désignent des fonctions abstraites du benchmark. Ils ne prétendent pas
reproduire toute la théorie FFWT, HGFM, CVCD ou OAK.

## Critères gelés R0.1

- exactement `4096` cellules;
- HGFM retrouve la même coordonnée que l’exhaustif;
- regret HGFM nul;
- moins de 20 % des cellules évaluées;
- regret glouton strictement positif;
- ablation HGFM à regret positif;
- ablation OAK choisissant une cellule quarantinée;
- ablation CVCD changeant la sélection;
- résultat déterministe et JSON strict.

Le fixture a été ajusté pendant le développement initial avant publication.
Il ne constitue donc pas un holdout aveugle ni une préinscription indépendante.
Les versions ultérieures devront geler les tenseurs et leurs empreintes avant
l'exécution par un évaluateur séparé.

## Commandes

```bash
python -m benchmarks.hgfm_tensorbench \
  --output out/hgfm-tensorbench/report.json
python -m unittest tests.test_hgfm_tensorbench -v
```

## Limites

- objectif et hyperarêtes synthétiques;
- information structurale fournie à HGFM;
- aucune donnée publique ou expérimentale;
- aucune preuve de transfert interdisciplinaire;
- aucun claim physique, commercial ou de sécurité;
- une réussite R0.1 autorise des benchmarks plus difficiles, pas une
  canonisation universelle.

## Promotion suivante

R0.2 doit geler plusieurs familles de tenseurs avant exécution, ajouter des
baselines d’optimisation reconnues, comptabiliser le coût de construction des
hyperarêtes, et faire évaluer les résultats par un tiers.
