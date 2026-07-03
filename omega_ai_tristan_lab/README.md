# Ω-AI-TRISTAN-LAB

Laboratoire agentique OAK-safe pour transformer l'IA en prototypes, preuves, actifs IP et revenus.

Ce module est conçu comme un **MIT++ de Tristan** : au lieu de produire seulement une attestation ou des notes de cours, il produit un pipeline reproductible :

```text
idée → théorie → prototype → tests → OAK → IP/revenus → action suivante
```

## Objectifs

- Formaliser les idées IA de Tristan en objets structurés.
- Générer des prototypes Python minimaux et testables.
- Évaluer les sorties avec un noyau OAK : exactitude, utilité, testabilité, risque, résidu.
- Transformer les hypothèses en décisions Bayes-Tristan multi-axes.
- Classer les actifs en open-source, publication, brevet, secret commercial, service, SaaS ou formation.
- Mapper les chemins de revenus sans surpromesse.
- Garder une mémoire négative des erreurs, limites et hallucinations.

## Architecture

```text
omega_ai_tristan_lab/
├── src/omega_ai_tristan_lab/
│   ├── models.py              # dataclasses canoniques
│   ├── oak_eval.py            # évaluation OAK
│   ├── bayes_tristan.py       # posterior tensoriel multi-score
│   ├── agent_harness.py       # boucle agentique plan→act→verify
│   ├── rag_engine.py          # RAG local minimal sans dépendance lourde
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
python -m pip install -e .
python -m pytest
```

## Exemple rapide

```bash
python -m omega_ai_tristan_lab.cli \
  --idea "Agent IA qui transforme un PDF scientifique en LaTeX, code, tests et rapport OAK"
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

## Prochaine évolution

1. Brancher GitHub Actions.
2. Ajouter un vrai index vectoriel optionnel.
3. Ajouter ingestion PDF/Markdown/LaTeX.
4. Ajouter OAKBench reproductible.
5. Ajouter un générateur de PR/prototype par théorie.
