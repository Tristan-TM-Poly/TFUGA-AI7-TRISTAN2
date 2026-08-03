# Ω-SUITE-FORM-T∞ R∞ — Hankel, Prony, hypergraphe et résidus

## 1. Objectif

Ce document décrit le second bloc du Genesis Pack R∞. Il ajoute quatre
mécanismes complémentaires :

1. diagnostics exacts de Hankel;
2. reconstruction spectrale rationnelle de Prony;
3. hypergraphe versionné de représentations;
4. décomposition récursive des résidus;
5. orchestration multi-familles.

Aucun de ces mécanismes ne transforme un préfixe fini en preuve globale.

---

## 2. Matrices de Hankel

Pour une suite `a_n`, la matrice de Hankel est :

```text
H[i,j] = a[i+j]
```

Un mélange fini d’exponentielles distinctes :

```text
a_n = Σ_(k=1)^r c_k λ_k^n
```

possède idéalement un rang de Hankel `r` lorsqu’un nombre suffisant de termes
exacts est disponible.

R∞ calcule :

- matrices rectangulaires ou carrées;
- rang exact par élimination rationnelle;
- déterminants exacts;
- profils de rang par taille;
- nullités;
- rang stable éventuel.

Le rang numérique avec seuil flottant n’est pas utilisé dans ce module. Une
future extension ajoutera une version par intervalles et SVD gardée par OAK.

### Exemple

```python
from fractions import Fraction
from omega_sequence_forms_t.rinf.hankel import hankel_rank_profile

terms = tuple(Fraction(2)**n + 3*Fraction(5)**n for n in range(20))
profile = hankel_rank_profile(terms, max_size=8)
assert profile.stable_rank == 2
```

---

## 3. Prony rationnel

R∞ cherche d’abord une récurrence constante minimale :

```text
a_n = c_1 a_(n-1) + ... + c_r a_(n-r)
```

Puis construit le polynôme caractéristique :

```text
x^r - c_1 x^(r-1) - ... - c_r
```

La première version spectrale accepte seulement une factorisation complète en
racines rationnelles distinctes.

Elle refuse explicitement :

- racines irrationnelles;
- paires complexes;
- racines répétées;
- systèmes sous-déterminés;
- extrapolation retenue incorrecte.

Cette restriction donne un noyau exact et simple. Les extensions futures
ajouteront :

- nombres algébriques;
- complexes exacts;
- multiplicités et facteurs polynomiaux en `n`;
- certification par intervalles;
- pencil matriciel numérique;
- Prony parcimonieux bruité.

### Exemple exact

```text
a_n = 2^n + 3·5^n
```

Récurrence :

```text
a_n = 7 a_(n-1) - 10 a_(n-2)
```

Polynôme :

```text
x² - 7x + 10 = (x-2)(x-5)
```

Forme spectrale retrouvée :

```text
a_n = 1·2^n + 3·5^n
```

Le candidat doit encore porter :

```json
{"global_identity_proved": false}
```

car la reconstruction vient d’un préfixe fini.

---

## 4. Hypergraphe de représentations

Le graphe possède des nœuds typés :

- séquence;
- forme;
- opérateur;
- fonction génératrice;
- asymptotique;
- intégrale;
- algorithme;
- preuve;
- résidu;
- contre-exemple;
- obligation de preuve.

Les hyperarêtes peuvent être :

- représente;
- transforme vers;
- compile vers;
- équivalent sous hypothèses;
- validé par;
- falsifié par;
- dépend de;
- résidu de;
- prouve;
- approxime.

Chaque arête conserve :

- sources;
- cibles;
- transformation;
- exactitude;
- invertibilité;
- hypothèses;
- obligations;
- preuves.

### Invariants

- une arête invertible doit être exacte;
- une arête `PROVES` ne peut pas être approximative;
- une arête `APPROXIMATES` ne peut pas être exacte;
- toutes les références doivent viser des nœuds existants;
- la sérialisation et le digest sont déterministes.

### Export GraphML

Les hyperarêtes sont projetées en arêtes source-cible pour GraphML, avec un
champ conservant l’identifiant de l’hyperarête originale.

---

## 5. Residual Form Evolution Engine

Soit un préfixe `a`. Après une première forme `F_1` :

```text
r^(1)_n = a_n - F_1(n)
```

Puis :

```text
r^(2)_n = r^(1)_n - F_2(n)
```

Finalement :

```text
a_n = F_1(n) + F_2(n) + ... + F_k(n) + r^(k)_n
```

Le moteur R∞ évalue chaque couche par :

```text
signal_gain - complexity_weight × complexity
```

Il arrête lorsque :

- aucun candidat n’existe;
- tous les candidats échouent sur le domaine;
- le gain marginal est insuffisant;
- une limite de couche de campagne est atteinte;
- le résidu est nul.

La limite de couche est optionnelle et opérationnelle. Elle n’est pas un
plafond permanent du programme.

### Round-trip

Le moteur vérifie :

```text
Σ couches(n) + résidu(n) = observation(n)
```

sur tout le préfixe observé.

### Fabriques initiales

- constante : première valeur, dernière valeur, moyenne;
- affine : droite déterminée par les deux premiers termes;
- périodique : périodes exactes jusqu’à un seuil de campagne.

Le système accepte des fabriques supplémentaires sans modifier le noyau.

---

## 6. Orchestrateur multi-familles

`discover_rinf` exécute actuellement :

- quasi-polynomial;
- rational-index;
- hypergeometric;
- P-recursive;
- rational-Prony;
- profil de rang de Hankel.

Il produit :

- candidats par famille;
- diagnostics;
- hypergraphe;
- digest du graphe;
- avertissements OAK;
- digest global du rapport.

### CLI

```bash
omega-sequence-forms-rinf orchestrate \
  "4,17,79,383,1891,9397,46879,234083" \
  --holdout 2 \
  --max-degree 4 \
  --max-order 5
```

### Limites

```text
max_period
max_degree
max_order
max_candidates_per_family
holdout
```

Ces limites contrôlent une exécution. Elles ne ferment pas le catalogue ou les
campagnes futures.

---

## 7. Tests adversariaux avancés

Les tests avancés vérifient :

- rang 1 d’une exponentielle;
- rang 2 d’un mélange de deux exponentielles;
- déterminant exact;
- convention du polynôme caractéristique;
- factorisation rationnelle;
- refus des racines répétées;
- refus des racines irrationnelles;
- reconstruction Prony et prédiction retenue;
- refus de Fibonacci par le Prony rationnel;
- hypergraphe valide;
- rejet des références inconnues;
- rejet d’une preuve approximative;
- export GraphML déterministe;
- résidu constant;
- résidu affine;
- résidu périodique;
- combinaison affine + périodique;
- seuil de gain;
- digest déterministe;
- orchestration multi-familles;
- absence systématique de prétention de preuve globale.

---

## 8. Prochaines extensions

### Spectral exact

- racines algébriques;
- facteurs irréductibles;
- racines complexes conjuguées;
- multiplicités;
- formes `P_j(n) λ_j^n`;
- décomposition de Jordan.

### Spectral numérique OAK

- SVD avec intervalles;
- matrix pencil;
- ESPRIT;
- Prony régularisé;
- sensibilité aux collisions;
- perturbations et conditionnement.

### Hypergraphe

- requêtes de chemins;
- équivalence bidirectionnelle;
- versionnage et diff;
- export JSON-LD/PROV-O;
- stockage append-only;
- intégration Rosette-Tristan.

### Résidus

- couches polynomiales;
- exponentielles;
- oscillations;
- quasi-polynômes;
- événements clairsemés;
- changements de régime;
- FFWT/CVCD;
- sélection Bayes-Tristan;
- front de Pareto.

---

## Invariant

> Le rang de Hankel, une factorisation spectrale, un graphe cohérent ou un
> résidu nul sur un préfixe sont des preuves de cohérence computationnelle sur
> les données fournies. Ils ne sont pas automatiquement une preuve de la loi
> infinie de la suite.
