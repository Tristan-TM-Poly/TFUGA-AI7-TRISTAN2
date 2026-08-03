# Ω-ANIME-SEASON-T∞ R4

## Le Huitième Feu — Saison 1

R4 transforme le format R3 de vingt minutes en une saison complète et vérifiable :

```text
12 épisodes × 20 minutes
= 240 minutes
= 14 400 secondes
= 144 scènes
= 1 368 plans
```

La saison est organisée en quatre phases de trois épisodes :

1. **Éveil** — découverte du Huitième Feu, de la dette causale et du nœud aveugle;
2. **Expansion** — temps manquant, mémoire urbaine et procès du Créancier;
3. **Fracture** — incarnation de l’Observatrice, guerre des permissions et réseau sous-marin;
4. **Confrontation** — monde sans témoins, dernière correction et transformation du Huitième Feu en protocole relationnel.

## Épisodes

| # | Titre | Phase | Dette ouverte |
|---:|---|---|---|
| 01 | La dette du réseau | Éveil | DEBT-NETWORK-001 |
| 02 | La Station des Absents | Éveil | DEBT-ABSENTS-002 |
| 03 | Le Nœud aveugle | Éveil | DEBT-BLIND-003 |
| 04 | Douze secondes manquantes | Expansion | DEBT-TIME-004 |
| 05 | La ville qui se souvient | Expansion | DEBT-MEMORY-005 |
| 06 | Le procès du Créancier | Expansion | DEBT-TRIAL-006 |
| 07 | L’Observatrice incarnée | Fracture | DEBT-BODY-007 |
| 08 | La guerre des permissions | Fracture | DEBT-PERMISSION-008 |
| 09 | Le réseau sous la mer | Fracture | DEBT-OCEAN-009 |
| 10 | Le monde sans témoins | Confrontation | DEBT-WITNESS-010 |
| 11 | La dernière correction | Confrontation | DEBT-LAST-011 |
| 12 | Le Huitième Feu | Confrontation | DEBT-SEASON2-001 |

Chaque épisode ferme la dette principale de l’épisode précédent avant d’en ouvrir une nouvelle. Le final ferme `DEBT-LAST-011` et conserve uniquement `DEBT-SEASON2-001`, afin d’ouvrir une saison 2 sans annuler la résolution de la saison 1.

## Architecture du bundle

```text
season.json
episode-index.jsonl
continuity-ledger.jsonl
causal-debt-ledger.jsonl
season-outline.md
season-dashboard.html
manifest.json
episodes/
  episode-01/
    timeline.json
    subtitles.fr.vtt
    edit-decision-list.csv
    audio-cues.jsonl
    episode-outline.md
    player.html
    manifest.json
  ...
  episode-12/
```

Le bundle contient exactement **91 fichiers** : 7 fichiers racine et 7 fichiers pour chacun des 12 épisodes.

## Commandes

```bash
python -m omega_anime_season_t validate-season-01
python -m omega_anime_season_t compile-season-01 \
  --output-dir generated/omega_anime_season_t/season_01_r4
pytest -q tests/test_omega_anime_season_t_r4.py
```

## Invariants OAK

- douze épisodes exactement;
- vingt minutes exactement par épisode;
- 114 plans et 12 scènes par épisode;
- hooks et conditions d’entrée identiques entre épisodes adjacents;
- aucune fermeture de dette inconnue;
- un seul résidu de dette après le final;
- titres, identifiants et questions principales uniques;
- génération byte-for-byte déterministe;
- lecteurs autonomes Canvas/WebAudio sans appel réseau;
- publication et fusion toujours humaines.

## Limites

R4 ne constitue pas douze épisodes animés terminés. Il s’agit d’une architecture de saison, de timelines, de lecteurs procéduraux et de preuves logicielles. La direction artistique, la réécriture, le jeu d’acteur, l’animation, le son final, la production, les licences, le financement et l’évaluation d’audience restent à réaliser et à valider humainement.
