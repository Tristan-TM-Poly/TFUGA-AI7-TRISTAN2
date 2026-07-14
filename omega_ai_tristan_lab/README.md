# Ω-AI-TRISTAN-LAB

Laboratoire agentique OAK-safe pour transformer l'IA en prototypes, preuves, actifs IP et revenus.

Ce module est conçu comme un **MIT++ de Tristan** : au lieu de produire seulement une attestation ou des notes de cours, il produit un pipeline reproductible :

```text
idée + documents → théorie → prototype → tests → OAK → IP/revenus → rapports persistants → action suivante
```

## Objectifs

- Formaliser les idées IA de Tristan en objets structurés.
- Ingerer des notes Markdown/texte et, optionnellement, des PDF avec dépendance explicite.
- Générer des prototypes Python minimaux et testables.
- Évaluer les sorties avec un noyau OAK : exactitude, utilité, testabilité, risque, résidu.
- Transformer les hypothèses en décisions Bayes-Tristan multi-axes.
- Classer les actifs en open-source, publication, brevet, secret commercial, service, SaaS ou formation.
- Mapper les chemins de revenus sans surpromesse.
- Persister `report.json`, `report.md` et `manifest.txt` dans un workspace.
- Garder une mémoire négative des erreurs, limites et hallucinations.

## Architecture

```text
omega_ai_tristan_lab/
├── src/omega_ai_tristan_lab/
│   ├── models.py              # dataclasses canoniques
│   ├── ingest.py              # ingestion texte/Markdown/PDF optionnel
│   ├── oak_eval.py            # évaluation OAK
│   ├── bayes_tristan.py       # posterior tensoriel multi-score
│   ├── agent_harness.py       # boucle agentique plan→act→verify
│   ├── rag_engine.py          # RAG local minimal sans dépendance lourde
│   ├── search_backends.py     # contrat backend lexical/vectoriel futur
│   ├── reporting.py           # JSON/Markdown renderers
│   ├── workspace.py           # persistence de runs
│   ├── ip_classifier.py       # filtre IP/publication/secret
│   ├── revenue_mapper.py      # chemins de revenu
│   ├── theory_to_prototype.py # idée brute → fiche prototype
│   └── cli.py                 # interface de base
├── tests/
├── examples/
├── docs/
├── reports/
└── benchmarks/
```

## Installation locale

```bash
cd omega_ai_tristan_lab
python -m pip install -e ".[dev]"
python -m pytest
```

PDF optionnel :

```bash
python -m pip install -e ".[dev,pdf]"
```

## Exemple rapide

```bash
python -m omega_ai_tristan_lab.cli \
  --idea "Agent IA qui transforme un PDF scientifique en LaTeX, code, tests et rapport OAK" \
  --pretty
```

## Exemple v0.2 avec workspace persistant

```bash
python -m omega_ai_tristan_lab.cli \
  --idea "Construire un agent OAK-safe qui digère mes notes IA" \
  --ingest docs/curriculum.md omega_ai_manifesto.md \
  --context-query "OAK IP revenus prototype" \
  --output-dir omega_runs
```

Sorties :

```text
omega_runs/<timestamp>_<slug>/
├── report.json
├── report.md
└── manifest.txt
```

## Statuts OAK

| Statut | Sens |
|---|---|
| IDEA | Fertile mais non testé |
| MODEL | Formalisé |
| PROTO | Codé minimalement |
| TESTED | Tests locaux passés |
| BENCHMARKED | Comparé à baseline |
| OAK_PASS | Robuste provisoirement |
| CANON | Intégré au corpus Tristan |
| IP_LOCK | À garder confidentiel |

## Règle de sécurité

Aucun résultat n'est présenté comme preuve forte sans test, baseline, incertitude et résidu. Les sorties du module sont des aides à la décision, pas des garanties de vérité, de revenus ou de brevetabilité.

## v0.2 ajouté

1. Ingestion locale texte/Markdown/LaTeX/Python/JSON/YAML.
2. PDF optionnel via `pypdf`, avec avertissement clair si dépendance absente.
3. Chunking avec provenance `source_path`, offsets et metadata.
4. Rendu JSON/Markdown.
5. Workspace persistant avec manifest OAK.
6. Backend de recherche lexical extensible vers vectoriel/hybride.
7. Tests couvrant ingestion, reporting, workspace et recherche.

## Prochaine évolution v0.3

1. Générateur automatique de skeleton prototype par `TheoryCard`.
2. Rapport OAKBench plus strict avec baselines.
3. Export GraphML/JSON-LD pour HGFM.
4. Ingestion ZIP de PDF pour Ω-PDF-HYPERGRAPH-GITHUB-T.
5. Générateur d'issues GitHub par résidu M⁻.
