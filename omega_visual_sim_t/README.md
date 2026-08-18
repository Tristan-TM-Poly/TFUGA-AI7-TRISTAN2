# Ω-VISUAL-SIM-T∞

Compilateur scientifique déterministe, traçable, attachable au web et désormais audiovisuel.
Le MVP R0.1 transforme un `VisualSpec` JSON en image SVG/PNG, GIF animé, manifeste
de provenance et rapport OAK. R0.2 ajoute une ABI `ExecutableWorld → SimCapsule`
pour brancher la simulation dans une interface interactive sans confondre rendu,
simulation et preuve. R0.3 ajoute `AudioVisualIR → MediaMicroscopeSlot` afin de
synchroniser vidéo, mots, phonèmes, représentations spectrales, amplitude, phase,
relations de phase, pitch et formants sans prétendre qu'une représentation candidate
est automatiquement vraie ou supérieure.

## Démonstration R0.1

```bash
cd omega_visual_sim_t
python -m omega_visual.cli render examples/oscillator.json --output build/demo
python -m omega_visual.cli verify build/demo/manifest.json
```

Artefacts produits : `preview.svg`, `preview.png`, `animation.gif`,
`states.json`, `manifest.json` et `oak_report.json`.

## R0.2 — ExecutableWorld / SimCapsule

Compiler le même modèle en capsule web attachable :

```bash
cd omega_visual_sim_t
python -m omega_visual.cli capsule examples/oscillator.json \
  --seed 7 \
  --output build/demo/capsule.json
```

Le contrat machine-readable `schema/executable-world.schema.json` sépare :

- identité, hypothèses et domaine de validité du monde;
- variables d'état et observables avec unités obligatoires;
- moteurs/capacités avec cible `client`, `remote` ou `hybrid`;
- niveau de fidélité `toy`, `analytical`, `rom`, `surrogate` ou `full_solver`;
- vues et transformations;
- contrôles interactifs;
- cinq familles d'incertitude;
- preuves, limites et statut scientifique.

`omega_visual.world.visual_spec_to_world()` lève le `VisualSpec` R0.1 existant dans
cette ABI sans inflation de claim. `compile_sim_capsule()` produit ensuite un objet
content-addressed portant notamment :

```text
protocol: OMEGA-SIM-ATTACH/0.2
attachment.slot: SimSlot
execution.streaming.state_stream: true
execution.streaming.view_stream: true
world_sha256: identité du contrat de monde
run_sha256: identité monde + seed
oak.simulation_is_proof: false
oak.visualization_is_truth: false
```

Une capsule peut ainsi devenir la charge utile stable d'un composant web `SimSlot`,
tandis que le calcul reste routable vers navigateur, worker distant ou mode hybride.
Le contrat d'attachement expose dès R0.2 les actions `inspect`, `fork`, `compare` et
`reset`; leur runtime UI complet reste une frontière suivante et non une capacité
prétendument déjà implémentée.

## R0.3 — AudioVisualIR / MediaMicroscope

`omega_visual.media` définit la première ABI audiovisuelle commune à l'analyse de
vidéos, au futur moteur FFWT et au site interactif :

```text
Video / audio source
→ upstream extraction
→ AudioVisualIR
   ├─ word + phoneme timeline
   ├─ representation portfolio
   │  ├─ FFT/STFT/CQT/WAVELET baseline
   │  └─ FFWT / FFWT-HAC candidate
   ├─ amplitude + phase
   ├─ relative phase graph
   ├─ pitch + formants
   ├─ scenes + semantic beats
   └─ provenance + rights + OAK
→ MediaMicroscopeSlot
```

Le contrat `schema/audio-visual-ir.schema.json` est volontairement une **IR**, pas un
faux analyseur : il reçoit des sorties calculées par des extracteurs/transformées en
amont et les rend synchronisables, comparables, traçables et testables. Les fonctions
`amplitude_phase()` et `relative_phase_graph()` fournissent les premières primitives
complexes exactes du noyau; le calcul FFWT complet reste un backend à qualifier contre
les baselines.

Gates R0.3 :

```text
FFWT candidate → baseline FFT/STFT/CQT/WAVELET obligatoire
FFWT / FFWT-HAC → amplitude + phase explicitement préservées
VERIFIED representation → evidence_refs non vides
absolute phase → jamais déclarée invariant
analysis → jamais promue en mesure instrumentale
representation → jamais promue en vérité
FFWT superiority → false tant qu'un OAKBench réel ne la démontre pas
```

`compile_media_capsule()` produit une capsule content-addressed :

```text
protocol: OMEGA-MEDIA-ATTACH/0.1
attachment.slot: MediaMicroscopeSlot
actions: inspect, seek, zoom, compare, fork, reset
panels: video, waveform, timeline, words, phonemes, amplitude, phase,
        phase_graph, pitch, formants
synchronization_key: time_s
```

Cette MRU rend donc possible une même coordonnée temporelle pour cliquer un mot ou un
phonème et synchroniser ensuite vidéo, waveform, spectre/FFWT, phase et variables
acoustiques. La resynthèse, l'extraction audio réelle et le viewer TypeScript complet
restent des capacités futures explicites.

## Garanties du MVP

- simulation déterministe d'un oscillateur harmonique amorti;
- unités et provenance obligatoires;
- aucun nombre scientifique inventé par le moteur de rendu;
- empreintes SHA-256 des entrées et sorties;
- rendu reproductible à paramètres identiques;
- animation calculée depuis les états simulés, jamais interpolée par IA;
- rapport OAK distinguant `SIMULATED` de `VERIFIED`;
- bornes explicites sur dimensions, cadence et nombre d'images;
- échappement des annotations SVG provenant de la spécification;
- schéma JSON versionné pour outillage et validation externe;
- ABI ExecutableWorld avec références de vues validées et unités non vides;
- statut `VERIFIED` refusé sans au moins un enregistrement de preuve;
- hash du monde séparé du hash d'exécution afin de rendre seed/cache explicites;
- incertitudes non quantifiées exportées comme résidus OAK visibles;
- AudioVisualIR content-addressed avec timeline phonème/mot et provenance;
- FFWT refusé comme candidat isolé sans baseline déclarée;
- FFWT `VERIFIED` refusé sans évidence;
- phase absolue séparée des relations de phase plus robustes.

## Contrats machine-readable

- R0.1 : `schema/visual-spec.schema.json`
- R0.2 : `schema/executable-world.schema.json`
- R0.2 publication : `schema/publication-fabric.schema.json`
- R0.3 média : `schema/audio-visual-ir.schema.json`

Le validateur d'exécution R0.1 applique en plus les contraintes physiques du solveur :
masse et raideur positives, amortissement non négatif et régime sous-amorti.
Le validateur `validate_executable_world()` R0.2 ajoute des gates sémantiques sans
dépendance externe : intégrité des identifiants, unités, références de vues, cibles
d'exécution, fidélité, incertitude et preuve minimale pour le statut `VERIFIED`.
`validate_audio_visual_ir()` R0.3 ajoute l'intégrité temporelle, les liens mot↔phonème,
le portefeuille de représentations, les droits/provenance et les gates OAK FFWT.

Le GIF reste une sortie de compatibilité. Les objets sources demeurent le `VisualSpec`,
la trajectoire `states.json`, l'`ExecutableWorld`, la `SimCapsule`, l'`AudioVisualIR`
et les capsules content-addressed.

## Frontière suivante

1. `SimSlot` + `MediaMicroscopeSlot` TypeScript/React consommant les protocoles canoniques.
2. extracteur vidéo/audio réel : audio track → transcription → phonème timeline → portfolio de transformées.
3. FFWT/FFWT-HAC backend réel avec OAKBench contre FFT/STFT/CQT/wavelets sur reconstruction, phase, compression et tâches vocales.
4. resynthèse contrôlée `Modify(parameter) → Render → Compare` avec conservation explicite des facteurs non ciblés.
5. SceneGraph/HGFM audiovisuel reliant timestamps, claims, équations, simulations et objets visuels.
6. registre de capacités et routeur `client ↔ remote ↔ hybrid`.
7. Adaptive Fidelity `toy → analytical → ROM → surrogate → full solver`.
8. StateStream/ViewStream/MediaStream effectifs avec cache par contenu.
9. bandes d'incertitude Bayes-Tristan et comparaisons expérimentales.
10. `Question/Theory/Video → ExecutableWorld + AudioVisualIR` sous OAK.
