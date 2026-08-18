# Ω-VISUAL-SIM-T∞ — Théorie de génération visuelle, simulationnelle et de mondes exécutables

## Proposition canonique

Une image scientifique est une projection contrôlée d'un état, d'un processus,
d'une structure ou d'une preuve. Une simulation est une sémantique exécutable sous
hypothèses; elle n'est ni une animation ni une preuve. Le pipeline canonique devient :

`objet → claims/hypothèses → ExecutableWorld → moteur(s) → état → vue → OAK → résidus`.

Une page web, un moteur et une visualisation ne sont donc pas les primitives. Ce sont
des projections d'un même objet épistémique exécutable.

## Invariants OAK

`réalisme visuel ≠ vérité scientifique`

`simulation ≠ preuve`

`visualisation ≠ validation expérimentale`

Chaque artefact porte son statut (`ARTISTIC`, `CONCEPTUAL`, `SCHEMATIC`,
`DATA_DRIVEN`, `SIMULATED`, `EXPERIMENTAL`, `VERIFIED`), ses unités, sa
provenance, ses limites, son domaine de validité, ses incertitudes et ses résidus.
Le statut `VERIFIED` exige une preuve enregistrée; une adaptation d'un ancien modèle
ne peut jamais promouvoir implicitement son statut.

## R0.1 — tranche verticale vérifiable

Le package `omega_visual_sim_t` compile un `VisualSpec` JSON d'oscillateur amorti
en SVG, PNG, GIF, états numériques, manifeste SHA-256 et rapport OAK. Cette tranche
reste le solveur/rendu de référence déterministe.

## R0.2 — Ω-SIMVIS-ATTACH / ExecutableWorld

R0.2 introduit l'ABI minimale génératrice :

```text
VisualSpec ──adapter──▶ ExecutableWorld ──compile──▶ SimCapsule
                           │                            │
                           │                            └─ OMEGA-SIM-ATTACH/0.2
                           ├─ state + observables          SimSlot
                           ├─ units                        inspect/fork/compare/reset
                           ├─ assumptions                  StateStream/ViewStream contract
                           ├─ engine capabilities          content hashes
                           ├─ execution target             OAK residues
                           ├─ fidelity
                           ├─ views
                           ├─ uncertainty
                           └─ evidence + limits
```

La `SimCapsule` est une projection web transportable de l'`ExecutableWorld`, pas le
monde lui-même. L'identité content-addressed du contrat de monde est séparée de
l'identité d'une exécution (`seed`), ce qui prépare cache, partage et reproductibilité.

## Méta-généralisation

La cible n'est pas un catalogue de simulateurs. La cible est une fabrique où la
question détermine la composition minimale de capacités :

`Question → WorldSpec → Representation → EngineGraph → Solve → View → Attack → OAK`.

Un simulateur peut donc devenir un artefact compilé just-in-time. À terme, un même
monde pourra arbitrer entre représentation analytique, ODE/DAE, PDE, particules,
agents, graphes, circuits, modèles réduits ou surrogates selon la question, le coût,
la latence, la fidélité et l'incertitude.

## Adaptive Fidelity

La fidélité est un axe de compilation :

`toy → analytical → ROM → surrogate → full_solver`

Le runtime pourra changer de niveau lorsque la question, le zoom sémantique ou le
budget l'exige. Toute transition doit conserver provenance, domaine de validité et
résidu; une approximation fluide ne doit jamais être affichée comme calcul haute
fidélité.

## Model / Solver Ecology

Plusieurs modèles et solveurs peuvent coexister. Le désaccord entre leurs prédictions
est un résidu scientifique prioritaire, non du bruit à masquer. Les futurs Solver et
Representation Tournaments doivent comparer exactitude, stabilité, coût, latence,
interprétabilité et domaine de validité sans transformer un score heuristique en preuve.

## Self-falsifying worlds

Une simulation avancée ne cherchera pas uniquement ses prédictions; elle cherchera
aussi ses propres frontières : paramètres où deux modèles divergent, violations
d'invariants, instabilités numériques, extrapolations et expériences discriminantes.

`best simulation = prediction + boundary discovery + falsification hooks`.

## Web Attachment

Le site interactif consomme un protocole stable plutôt que les détails internes de
chaque moteur. La primitive UI cible est `SimSlot`. Une capsule annonce ses contrôles,
vues, cible d'exécution, flux, statut OAK et identités de reproductibilité. Le calcul
pourra être local, distant ou hybride sans coupler le frontend à un solveur particulier.

## Frontière suivante

1. implémenter `SimSlot` côté TypeScript/React;
2. créer un registre de capacités et un `SimulationRouter`;
3. rendre StateStream/ViewStream effectifs;
4. ajouter Adaptive Fidelity et cache content-addressed de sessions;
5. introduire SceneGraph/HGFM et Semantic Zoom;
6. visualiser séparément incertitudes paramétrique, expérimentale, numérique,
   structurelle et d'extrapolation;
7. ajouter Solver/Representation Tournament;
8. compiler `Question → ExecutableWorld` et `Theory → ExecutableWorld`;
9. connecter le Residual Field à un Experiment Compiler;
10. maintenir `LocalPASS ≠ GlobalPASS` lors des couplages multi-moteurs.

## Doctrine terminale

Ne pas construire un site contenant des simulations. Construire un site dans lequel
toute connaissance suffisamment formalisée peut devenir un monde exécutable,
manipulable, comparable, falsifiable et partageable — tout en laissant visible la
frontière entre modèle, calcul, visualisation, expérience et réalité.
