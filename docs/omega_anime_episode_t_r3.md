# Ω-ANIME-EPISODE-T R3

## Format canonique : épisodes de 20 minutes

`Ω-ANIME-EPISODE-T R3` transforme l'animatique R2 de trois minutes en un premier épisode complet de **1 200 secondes exactement**.

La règle n'est pas d'étirer mécaniquement le pilote. Les 180 secondes déjà validées deviennent l'ouverture froide, puis 1 020 secondes nouvelles développent les conséquences, l'enquête, le contre-mouvement, la dette causale, le choix moral, l'épilogue et la promesse de l'épisode suivant.

## Épisode 1

**Titre :** *La dette du réseau*

```text
00:00–03:00  Ouverture froide R2 conservée
03:00–04:00  Titre et promesse de série
04:00–08:00  Après la correction
08:00–12:00  La trace de l'Observatrice
12:00–16:00  Le contre-mouvement
16:00–18:30  La dette prend forme
18:30–19:30  Choisir une limite
19:30–20:00  Épilogue et prochain épisode
```

Le modèle concret contient **12 scènes** et **114 plans**. Les sept nouvelles scènes contiennent douze plans chacune; les trente plans initiaux restent identiques au modèle R2.

## Artefacts GitHub

Le compilateur produit :

- `episode-01.html` — lecteur Canvas/WebAudio autonome;
- `timeline.json` — 1 200 secondes, 12 scènes, 114 plans;
- `storyboard-contact-sheet.svg` — 114 panneaux;
- `subtitles.fr.vtt` — jusqu'à `00:20:00.000`;
- `edit-decision-list.csv`;
- `audio-cues.jsonl`;
- `episode-outline.md`;
- `manifest.json` avec hashes SHA-256.

## Commandes

```bash
python -m omega_anime_episode_t validate-episode-01
python -m omega_anime_episode_t compile-episode-01 \
  --output-dir generated/omega_anime_episode_t/episode_01_r3
pytest -q tests/test_omega_anime_episode_t_r3.py
```

## OAK

R3 prouve la durée, la continuité, la structure, le déterminisme et la génération des artefacts. R3 ne prouve pas encore la qualité d'une animation finale, la performance vocale, la demande d'une audience, le budget, la clearance juridique ou la capacité d'un studio à produire la saison.
