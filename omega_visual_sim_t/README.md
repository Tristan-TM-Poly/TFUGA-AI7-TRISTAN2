# Ω-VISUAL-SIM-T∞

Compilateur visuel scientifique déterministe, traçable et désormais attachable au web.
Le MVP R0.1 transforme un `VisualSpec` JSON en image SVG/PNG, GIF animé, manifeste
de provenance et rapport OAK. R0.2 ajoute une ABI `ExecutableWorld → SimCapsule`
pour brancher la simulation dans une interface interactive sans confondre rendu,
simulation et preuve.

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
- incertitudes non quantifiées exportées comme résidus OAK visibles.

## Contrats machine-readable

- R0.1 : `schema/visual-spec.schema.json`
- R0.2 : `schema/executable-world.schema.json`

Le validateur d'exécution R0.1 applique en plus les contraintes physiques du solveur :
masse et raideur positives, amortissement non négatif et régime sous-amorti.
Le validateur `validate_executable_world()` R0.2 ajoute des gates sémantiques sans
dépendance externe : intégrité des identifiants, unités, références de vues, cibles
d'exécution, fidélité, incertitude et preuve minimale pour le statut `VERIFIED`.

Le GIF reste une sortie de compatibilité. Les objets sources demeurent le `VisualSpec`,
la trajectoire `states.json`, l'`ExecutableWorld` et la `SimCapsule` content-addressed.

## Frontière suivante

1. `SimSlot` TypeScript/React consommant directement `OMEGA-SIM-ATTACH/0.2`.
2. registre de capacités et routeur `client ↔ remote ↔ hybrid`.
3. SceneGraph/HGFM générique et adaptateurs champs, tenseurs et hypergraphes.
4. Adaptive Fidelity `toy → analytical → ROM → surrogate → full solver`.
5. StateStream/ViewStream effectifs avec reprise de session et cache par contenu.
6. bandes d'incertitude Bayes-Tristan et comparaisons expérimentales.
7. Solver/Representation Tournament et résidus de désaccord.
8. `Question → ExecutableWorld` et `Theory → ExecutableWorld` sous OAK.
