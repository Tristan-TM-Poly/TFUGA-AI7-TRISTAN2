# Ω-ANIME-ANIMATIC-T R2

## Le Huitième Feu — premier artefact regardable

R2 transforme le ShotGraph validé de R1 en un animatique procédural de 180 secondes. Le livrable central est un fichier HTML autonome utilisant Canvas et WebAudio, sans dépendance réseau, accompagné d’une timeline JSON, d’un storyboard SVG, de sous-titres WebVTT, d’une EDL CSV, de repères audio JSONL, d’un manifeste SHA-256 et d’un rapport OAK.

## Pipeline

```text
Ω-ANIME-STUDIO-T R1
  → 5 scènes / 30 plans
  → timeline contiguë
  → intentions visuelles et sonores
  → lecteur Canvas/WebAudio
  → storyboard contact sheet
  → VTT + EDL + audio cues
  → manifeste et preuves GitHub Actions
```

## Commandes

```bash
python -m omega_anime_animatic_t validate-demo
python -m omega_anime_animatic_t compile-demo \
  --output-dir generated/omega_anime_animatic_t/eighth_fire_r2
pytest -q tests/test_omega_anime_animatic_t_r2.py
```

## Artefacts

- `timeline.json` — montage machine-readable;
- `eighth-fire-animatic.html` — lecteur autonome;
- `storyboard-contact-sheet.svg` — 30 cartes de plans;
- `subtitles.fr.vtt` — sous-titres et descriptions guides;
- `edit-decision-list.csv` — décisions de montage;
- `audio-cues.jsonl` — repères sonores synthétiques;
- `manifest.json` — hashes et invariants;
- `report.md` — frontière épistémique.

## Ce que R2 démontre

- une durée exactement égale à 180 secondes;
- 30 plans contigus distribués sur 5 scènes;
- une intention, un cadrage, un mouvement, une légende et un repère sonore par plan;
- un lecteur sans appels réseau;
- une génération déterministe et testable;
- un premier objet audiovisuel consultable.

## Ce que R2 ne démontre pas

- animation finale;
- jeu d’acteur validé;
- qualité artistique ou émotionnelle;
- demande du public;
- clearance juridique complète;
- faisabilité budgétaire d’une production professionnelle;
- vérité scientifique des éléments de fiction.

## M⁻ intégrée

L’échec du transport R2 initial est conservé comme mémoire négative : des fragments opaques et des matérialiseurs temporaires ne doivent pas devenir l’architecture normale. Le code source lisible, les tests et les artefacts GitHub Actions constituent désormais la voie canonique.
