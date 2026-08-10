# Ω-VISUAL-SIM-T∞

Compilateur visuel scientifique déterministe et traçable. Le MVP transforme un
`VisualSpec` JSON en image SVG/PNG, GIF animé, manifeste de provenance et rapport
OAK. Il sépare explicitement illustration, schéma, données, simulation et preuve.

## Démonstration

```bash
cd omega_visual_sim_t
python -m omega_visual.cli render examples/oscillator.json --output build/demo
python -m omega_visual.cli verify build/demo/manifest.json
```

Artefacts produits : `preview.svg`, `preview.png`, `animation.gif`,
`states.json`, `manifest.json` et `oak_report.json`.

## Garanties du MVP

- simulation déterministe d'un oscillateur harmonique amorti;
- unités et provenance obligatoires;
- aucun nombre scientifique inventé par le moteur de rendu;
- empreintes SHA-256 des entrées et sorties;
- rendu reproductible à paramètres identiques;
- animation calculée depuis les états simulés, jamais interpolée par IA;
- rapport OAK distinguant `SIMULATED` de `VERIFIED`.
- bornes explicites sur dimensions, cadence et nombre d'images;
- échappement des annotations SVG provenant de la spécification;
- schéma JSON versionné pour outillage et validation externe.

## Contrat VisualSpec

Le contrat machine-readable se trouve dans `schema/visual-spec.schema.json`. Le
validateur d'exécution applique en plus les contraintes physiques du solveur :
masse et raideur positives, amortissement non négatif et régime sous-amorti.

Le GIF est une sortie de compatibilité. Le modèle source demeure le VisualSpec et
la trajectoire `states.json`.
