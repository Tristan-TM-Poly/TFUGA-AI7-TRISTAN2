# Ω-RE-T∞ — Reverse Engineering de Tristan

## Statut

Prototype de recherche OAK-safe pour petits systèmes synthétiques, possédés ou expressément autorisés. Il reconstruit une classe de comportements compatibles avec les observations; il ne prétend pas retrouver un original interne unique lorsque le problème est non identifiable.

## Boucle opérationnelle

```text
observer → hypothétiser → choisir une expérience discriminante
→ mesurer → éliminer ou réviser → reconstruire → falsifier
```

La sortie conserve le posterior, la dette d’identifiabilité, la provenance, les résidus et le statut OAK.

## MVP R0.1

Le premier banc d’essai reconstruit une machine de Mealy cachée à partir de requêtes entrée-sortie.

Fonctions :

1. énumération exacte de petits espaces de machines;
2. observations typées;
3. vraisemblance et posterior Bayésien;
4. sélection active par gain d’information attendu;
5. classes d’équivalence comportementale;
6. dette d’identifiabilité;
7. jumeau contrefactuel probabiliste;
8. registre de preuve append-only chaîné par SHA-256;
9. spécification clean-room;
10. OAKGate fail-closed;
11. benchmark déterministe actif contre passif;
12. CLI reproductible.

## Exécution

```bash
python -m pytest -q tests/test_omega_re_*.py
python -m omega_re_t.cli demo
python -m omega_re_t.cli benchmark --cases 16
```

Après installation du projet :

```bash
omega-re demo
omega-re benchmark --cases 32 --output reports/omega-re-benchmark.json
```

## Modèle mathématique

Une machine candidate est définie par

\[
M=(S,\Sigma,\Gamma,\delta,\lambda,s_0).
\]

Pour une expérience \(x\), les candidats sont partitionnés par leur sortie prédite. Le planificateur choisit

\[
x^*=\arg\max_x\left[I(M;Y\mid x)-C(x)-R(x)-L(x)\right].
\]

## Statuts épistémiques

`OBSERVED`, `MEASURED`, `DERIVED`, `INFERRED`, `PLAUSIBLE`, `RECONSTRUCTED`, `VERIFIED`, `FALSIFIED`, `UNKNOWN`.

La fidélité seule ne permet jamais la promotion `VERIFIED`; une validation indépendante est requise.

## Architecture

```text
omega_re_t/
├── models.py
├── fsm.py
├── bayes.py
├── active.py
├── identifiability.py
├── evidence.py
├── twin.py
├── cleanroom.py
├── oak.py
├── campaign.py
├── benchmark.py
└── cli.py
```

## Limites R0.1

- espace fini, discret et déterministe;
- remise à zéro avant chaque séquence;
- alphabets connus;
- recherche exhaustive réservée aux petits espaces;
- bruit modélisé simplement;
- résultats limités au domaine des expériences exécutées;
- aucun résultat sur un système tiers réel.

## Frontière R0.2

- automates probabilistes et temporels;
- recherche de structure sans énumération exhaustive;
- coûts, bruit et budgets adaptatifs;
- RE-IR JSON;
- minimisation et preuves d’équivalence;
- formats et protocoles jouets générés localement;
- généalogie de versions synthétiques;
- calibration de l’incertitude;
- checkpoints et mémoire négative persistante.
