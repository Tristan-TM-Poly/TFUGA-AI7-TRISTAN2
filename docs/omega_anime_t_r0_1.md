# Ω-ANIME-T∞ R0.1

## Animés hypergraphiques de Tristan

**Statut :** architecture créative et prototype logiciel OAK-safe.

Ω-ANIME-T∞ transforme une idée d'animé en un paquet de préproduction structuré, testable, versionné et révisable. R0.1 ne prétend ni mesurer automatiquement la qualité artistique, ni remplacer une équipe humaine, ni garantir une audience. Il vérifie des propriétés internes minimales avant de dépenser davantage en production.

## 1. Problème traité

Un univers peut croître beaucoup plus vite qu'un épisode ne peut être terminé. Les échecs visés sont :

- lore massif sans scène produite;
- personnages définis uniquement par leurs pouvoirs;
- pouvoirs sans coût ni contre-mesure;
- mystères sans classe de résolution;
- exposition encyclopédique;
- continuité fragile;
- actifs générés sans provenance ni contrôle IP;
- saison planifiée avant preuve par animatique.

La règle R0.1 est donc :

> Une branche créative ne progresse pas par le nombre de concepts, mais par un artefact temporel que des humains peuvent regarder, comprendre, critiquer et réviser.

## 2. Objets exécutables

### `AnimeProject`

Contient logline, question thématique, audience, format, durée, invariants visuels, règles du monde, personnages, beats, promesses, risques, prochaines actions et statut OAK.

### `CharacterState`

Encode désir, besoin, peur, contradiction, pouvoir, limitation, connaissances et relations. Le modèle force explicitement une limitation pour chaque pouvoir.

### `EpisodeBeat`

Chaque beat contient : objectif, conflit, changement irréversible, information révélée et durée estimée. Une scène sans conflit ou sans changement est rejetée par le modèle.

### `NarrativePromise`

Le registre relie introduction, préparation, payoff attendu et état `OPEN`, `PARTIAL`, `RESOLVED` ou `ABANDONED`.

### `NarrativeLinter`

Détecte notamment :

- modèle invalide;
- absence totale de flux d'information;
- surcharge de personnages dans un format court;
- dette excessive de promesses;
- changements irréversibles dupliqués;
- pouvoir et limite confondus;
- absence de registre des risques.

Les résultats sont des indicateurs de revue. Une absence de finding ne prouve pas qu'une œuvre est bonne.

## 3. Projet fondateur : Le Huitième Feu

Le démonstrateur est un pilote de 180 secondes.

**Logline :** un étudiant qui perçoit les relations invisibles entre les systèmes sauve son laboratoire par une correction minuscule, puis découvre qu'il a déplacé le danger ailleurs.

**Question :** peut-on améliorer un système sans devenir responsable de toutes ses conséquences?

Le pilote contient cinq beats :

1. une anomalie est rejetée comme bruit;
2. un réseau causal devient brièvement visible;
3. une correction locale évite une panne;
4. la contrainte réapparaît ailleurs;
5. une observatrice inconnue nomme le Huitième Feu.

Le pouvoir central révèle ou reconfigure temporairement des relations. Il ne crée ni matière ni énergie. Toute intervention garde un coût, une incertitude ou une dette causale.

## 4. Exécution

```bash
omega-anime show-demo
omega-anime lint-demo
omega-anime compile-demo \
  --output-dir generated/omega_anime_t/eighth_fire_r0_1
```

L'exécution directe sans installation reste disponible avec `python -m omega_anime_t`.

Le bundle contient :

```text
project.json
oak-lint.json
manifest.json
report.md
```

`project.json` est la source narrative structurée. `oak-lint.json` contient la décision déterministe. `manifest.json` conserve les empreintes SHA-256. `report.md` résume le statut et les limites.

## 5. Statuts OAK

- `EXPLORATORY` : idée fertile non formalisée;
- `FORMALIZED` : objets, règles et risques structurés;
- `SIMULATED` : storyboard ou animatique minuté;
- `DEMONSTRATED` : test d'audience avec baseline et conditions d'échec;
- `REPLICATED` : second panel ou revue indépendante;
- `CANONICAL` : validation humaine, IP, faisabilité et archivage.

Le démonstrateur reste `FORMALIZED`. La présence d'un script et de tests ne constitue pas encore un animatique, une validation de marché ou une œuvre publiée.

## 6. Gates de production

R0.1 exige :

- un seul artefact primaire par session importante;
- pilote avant saison;
- animatique avant animation haute fidélité;
- revue humaine de tout contenu généré;
- IPGate avant publication;
- aucun style d'artiste vivant demandé ou copié directement;
- provenance des polices, musiques, voix, images et modèles;
- approbation explicite pour publication, contrat, licence ou suppression irréversible.

## 7. Tests

Le banc vérifie :

- validité du projet canonique;
- durée exacte de trois minutes;
- limites distinctes pour chaque pouvoir;
- absence de finding bloquant;
- détection de l'absence de flux d'information;
- détection d'un registre de risques vide;
- ordre unique des beats;
- contraintes des statuts OAK;
- sérialisation JSON;
- déterminisme du bundle et de son manifeste.

## 8. Prochaine cristallisation

La transition utile n'est pas une multiplication de séries. Elle est :

```text
R0.1 projet structuré
→ shot-list de 24 à 36 plans
→ storyboard basse fidélité
→ animatique 180 s
→ test de compréhension
→ mémoire M⁺/M⁻
→ réécriture
```

Le passage à `SIMULATED` exigera un fichier de shot-list, des durées réellement mesurées et un artefact audiovisuel ou une animatique reproductible.
