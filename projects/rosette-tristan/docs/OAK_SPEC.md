# OAK Spec — Rosette-Tristan

## Axiomes

- OCR ≠ vérité.
- Résumé ≠ preuve.
- Code compilé ≠ modèle validé.
- Ressemblance LaTeX ≠ équivalence mathématique.

## Vérifications minimales

1. Chaque bloc conserve une trace source : chemin, page si disponible, span ou bbox si disponible.
2. Chaque artefact a une confiance et un statut OAK.
3. Les ambiguïtés vont dans M⁻ au lieu d’être cachées.
4. Les sorties publiques ne doivent pas republier de longs passages protégés.
5. Code et reproduction restent hypothèses jusqu’aux tests.

## Modes

- `strict`: bloque ou marque sévèrement les artefacts sans source/confiance suffisante.
- `research`: génère plus largement, mais marque les incertitudes.
- `creative`: permet extensions Tristan, en séparant source et invention.
