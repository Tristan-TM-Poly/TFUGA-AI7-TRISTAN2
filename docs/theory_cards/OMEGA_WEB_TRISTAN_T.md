# Ω-WEB-TRISTAN-T

## Système Internet vivant des théories, preuves, prototypes et actifs de Tristan

**Version:** R0.1  
**Date:** 2026-08-02  
**Statut:** prototype public statique, OAK-safe  
**Implémentation:** `apps/tristan-8fire-site/`

## 1. Phrase-mère

Le site de Tristan n’est pas une collection de grandes affirmations. C’est un graphe navigable de propositions, preuves, codes, limites, résultats négatifs et actifs.

```text
idée -> théorie -> claim -> preuve/test -> code -> prototype -> usage -> produit/publication/IP
```

## 2. Problème

Un corpus transdisciplinaire massif devient difficile à comprendre, vérifier et utiliser lorsque :

- les visions et résultats démontrés utilisent le même langage;
- les théories ne pointent pas vers leurs tests et artefacts;
- les résultats négatifs disparaissent;
- la publication précède l’analyse IP, vie privée ou sécurité;
- le nombre de branches remplace la mesure des actifs terminés.

## 3. Objets canoniques

Chaque élément public doit devenir un objet structuré :

- théorie;
- claim;
- définition;
- équation;
- source;
- expérience;
- benchmark;
- code;
- résultat;
- résidu;
- mémoire négative M-;
- produit, service ou piste IP.

Relations minimales :

```text
derive_de, implemente, teste, soutient, limite, refute,
depend_de, genere, protege, commercialise
```

## 4. États épistémiques

```text
vision
hypothèse
architecture
brouillon_code
prototype
testé
reproduit
validé_partiellement
réfuté
produit
```

Une interface ne doit jamais promouvoir automatiquement un objet vers un état supérieur. La promotion exige une preuve versionnée et révisable.

## 5. Vecteur OAK

```text
OAK(x) = [vérité, utilité, testabilité, simplicité, valeur, protection]
```

Les composantes sont des signaux de navigation provisoires. Elles ne sont ni des probabilités de vérité, ni une preuve, ni une valorisation financière.

## 6. Portes de publication

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Le jeu de données public exclut par défaut :

- données personnelles non nécessaires;
- inventions non protégées;
- secrets commerciaux;
- données sensibles;
- affirmations sans statut ou limites;
- actions autonomes irréversibles.

## 7. Trois profondeurs futures

1. **Simple externe** — problème, utilité, état, démonstration.
2. **Technique standard** — définitions, équations, algorithmes, benchmarks.
3. **Tristan complet** — hypergraphe, branches exploratoires, M+/M-, IP et dépendances.

R0.1 expose une seule couche publique prudente. Les couches privées ou partenaires ne sont pas implémentées.

## 8. Implémentation R0.1

Le prototype fournit :

- HTML sémantique et accessible;
- design responsive sans dépendance externe;
- huit cartes de théories représentatives;
- recherche plein texte locale;
- filtres par maturité et domaine;
- profils OAK;
- limites et prochaine action;
- métriques publiques minimales;
- test de cohérence du dataset.

## 9. Invariants OAK-Web

- Une théorie nommée n’est pas une théorie validée.
- Une architecture n’est pas un prototype.
- Un prototype n’est pas un produit.
- Une reconstruction plausible n’est pas une preuve.
- Un score OAK n’est pas une probabilité.
- Un lien vers GitHub n’est pas une validation scientifique.
- Un résultat négatif utile doit rester visible.
- Toute métrique publique doit pouvoir être recalculée.
- Toute donnée publique doit avoir un propriétaire, une provenance et un statut.

## 10. Tests de promotion vers R0.2

R0.2 exige au minimum :

1. génération des cartes depuis des schémas canoniques;
2. liens exacts claim -> test -> commit -> résultat;
3. validation JSON Schema;
4. contrôle des liens morts;
5. audit d’accessibilité;
6. version française et anglaise reliée à une source canonique;
7. aperçu de déploiement reproductible;
8. IPGate documenté pour chaque nouvelle branche publiée.

## 11. Mémoire négative initiale

```text
M-1: afficher beaucoup de branches peut simuler le progrès.
Correction: afficher artefacts, tests, résultats négatifs et prochaines actions.

M-2: un score unique peut cacher une faiblesse critique.
Correction: conserver un vecteur OAK multidimensionnel.

M-3: publier automatiquement peut exposer IP ou données privées.
Correction: quatre portes de publication et revue humaine.
```

## 12. Commande canonique

```text
GO WEB-CAPTURE
-> GO WEB-CANON
-> GO WEB-OAK
-> GO WEB-BUILD
-> GO WEB-TEST
-> GO WEB-IPGATE
-> GO WEB-PREVIEW
-> GO WEB-PUBLISH
```

Le dernier état reste explicitement humain et autorisé.
