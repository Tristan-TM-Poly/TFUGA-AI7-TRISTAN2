# ChatGPT × Tristan OS Interface

Interface statique personnalisée pour préparer des prompts ChatGPT adaptés à l’écosystème Tristan : TFUGA, HGFM, OAK, SAGE, Bayes-Tristan, Publication Atlas, Open Data Harvester, Spectro Lab et GitHub Builder.

## Ce que c’est

- Un cockpit local de composition de prompts.
- Une interface sans dépendances externes.
- Un outil review-only et OAK-safe.
- Un gestionnaire de sessions locales via `localStorage`.
- Un export/import JSON de sessions.

## Ce que ce n’est pas

- Ce n’est pas une modification de l’application officielle ChatGPT.
- Ce n’est pas un client API OpenAI.
- Ce n’est pas un système d’envoi automatique.
- Ce n’est pas une preuve que les théories sont validées.

## Lancer localement

Ouvrir simplement :

```text
interfaces/chatgpt-tristan/index.html
```

ou servir statiquement le dossier :

```bash
python -m http.server 8000
```

puis ouvrir :

```text
http://localhost:8000/interfaces/chatgpt-tristan/
```

## Fonctions

- Modes SAGE : Architect, OAK Verifier, GitHub Builder, Publication Atlas, Open Data Harvester, Spectro Lab, Math Proof.
- Branches Tristan sélectionnables.
- Actions repo : fichiers, tests, workflows, docs, runbooks, benchmarks.
- Qualité OAK : statut de claim, résidus, prototypes, sécurité.
- Prompt généré prêt à copier dans ChatGPT.
- Sessions locales sauvegardées dans le navigateur.
- Export/import JSON.

## OAK boundary

Chaque prompt généré rappelle :

- vision fertile ≠ formalisation ≠ prototype ≠ mesure ≠ preuve;
- M− negative memory;
- pas de promesse de travail futur;
- ZÉRO-TOUCH quand les outils le permettent;
- produire des artifacts vérifiables quand possible.
