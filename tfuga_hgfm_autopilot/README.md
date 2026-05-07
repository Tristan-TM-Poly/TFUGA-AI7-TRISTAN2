# TFUGA HGFM Autopilot

Paquet minimal d'automatisation controlee pour TFUGA / AI-7 / TRISTAN2.

Objectif: convertir une idee, une note vocale, un fichier LaTeX ou un changement de code en cycle propre: detection, verification, tests, commit local, puis push optionnel.

## Contenu

- `.github/workflows/hgfm_autopilot.yml`: validation GitHub Actions.
- `tfuga_hgfm_autopilot/scripts/hgfm_watch.py`: watcher local de moindre action.
- `tfuga_hgfm_autopilot/tests/test_hgfm_watch.py`: tests de base.
- `tfuga_hgfm_autopilot/requirements.txt`: dependances minimales.

## Usage local

Validation unique:

```bash
python tfuga_hgfm_autopilot/scripts/hgfm_watch.py . --once --dry-run
```

Commit local si changements valides:

```bash
python tfuga_hgfm_autopilot/scripts/hgfm_watch.py . --once
```

Boucle autonome avec verification horaire:

```bash
python tfuga_hgfm_autopilot/scripts/hgfm_watch.py . --interval 3600
```

Boucle autonome avec publication explicite:

```bash
python tfuga_hgfm_autopilot/scripts/hgfm_watch.py . --interval 3600 --push
```

Doctrine: automatiser l'effort, pas automatiser le risque.
