# Ω-PDF-HYPERGRAPH-GITHUB-T / AIT-Frédéric

## Mission

Construire le système qui absorbe un corpus massif de PDF, ZIP, Markdown, code et notes, puis le transforme en mémoire hypergraphique OAK-safe utilisable dans GitHub.

La boucle canonique est :

```text
Drive/ZIP/PDF/code -> manifest/hash -> extraction -> chunks page/bbox -> claim candidates -> HGFM hyperedges -> CVCD targets -> OAK report -> GitHub artifacts/issues/prototypes
```

## Règle OAK fondamentale

Une extraction n'est pas une preuve. Une reconstruction n'est pas une vérité. Un hypergraphe généré automatiquement est un graphe de candidats jusqu'à validation.

Le système garde donc, pour chaque fragment :

- provenance : fichier, conteneur, hash, page, offset;
- méthode : texte brut, PDF text layer, OCR futur, parseur code;
- confiance : score d'extraction et avertissements;
- statut : raw extraction, claim candidate, evidence, residue, canon;
- risques : IP, brevet, confidentialité, sécurité, médical, haute tension, laser;
- OAK gate : publishable=false par défaut.

## MVP GitHub ajouté

Le module `omega_prof_poly_t.universal_absorber` ajoute :

- ingestion de fichiers, dossiers et ZIP;
- extraction texte pour `.md`, `.txt`, `.json`, `.yaml`, `.py`, `.tex`, etc.;
- extraction PDF optionnelle via `pypdf` si disponible;
- chunking overlapé avec identifiants stables;
- détection heuristique de claims, risques, tags HGFM/CVCD/OAK/IP/prototype;
- export `manifest.json`, `chunks.jsonl`, `claims.jsonl`, `hypergraph.json`, `hypergraph.graphml`, `oak_report.json`;
- CLI `omega-corpus-absorb` en mode dry-run.

## Commande locale

```bash
omega-corpus-absorb path/to/corpus_or_zip --output-dir generated/omega_corpus
```

Sorties :

```text
generated/omega_corpus/manifest.json
generated/omega_corpus/chunks.jsonl
generated/omega_corpus/claims.jsonl
generated/omega_corpus/hypergraph.json
generated/omega_corpus/hypergraph.graphml
generated/omega_corpus/oak_report.json
```

## Architecture cible v2

### 1. Source adapters

- `local_dir_adapter` : dossiers locaux;
- `zip_adapter` : archives ZIP;
- `drive_manifest_adapter` : liste Google Drive autorisée;
- `pdf_text_adapter` : couche texte PDF;
- `ocr_adapter` : OCR séparé et coûteux, jamais confondu avec extraction sûre;
- `code_adapter` : AST, fonctions, classes, dépendances;
- `notebook_adapter` : cellules, sorties, figures;
- `github_adapter` : fichiers, issues, PR, commits.

### 2. Rosette extraction tensor

Chaque extraction reçoit un tenseur :

```text
R = {source, page, bbox, method, confidence, language, modality, risk, rights, residue}
```

### 3. Claim-Evidence-Residue graph

Chaque claim doit relier :

```text
claim -> evidence chunks -> method/proof/test -> counter-evidence/residue -> OAK status
```

### 4. CVCD compression

Les chunks sont compressés vers :

- invariants fertiles;
- définitions réutilisables;
- prototypes possibles;
- tests falsifiables;
- mémoire négative M⁻;
- canon minimal.

### 5. GitHub sync OAK-safe

GitHub ne doit recevoir que :

- code du pipeline;
- manifestes non sensibles;
- rapports OAK nettoyés;
- issues d'action;
- tests;
- schémas.

Les PDF originaux, données privées, inventions brevetables et contenus confidentiels restent hors dépôt public.

## Mémoire négative M⁻ obligatoire

Le système doit mémoriser :

- PDF sans texte extractible;
- pages OCR incertaines;
- claims sans preuve;
- doublons;
- contradictions;
- hallucinations de reconstruction;
- risques IP/publiques;
- fichiers corrompus;
- sources non autorisées;
- métriques trop belles pour être vraies.

## Prochaines extensions

1. Ajouter `pypdf` en dépendance optionnelle et test PDF fixture minimal.
2. Ajouter extraction page-level avec bbox quand l'outil PDF le permet.
3. Ajouter OCR séparé avec budget, avertissements et confidence tensor.
4. Ajouter `drive_manifest_adapter` avec OAuth least privilege.
5. Ajouter `github_issue_emitter` en dry-run puis gated-approval.
6. Ajouter `cvcd_canonizer` qui produit définitions, tests et prototypes.
7. Ajouter `m_minus_registry.jsonl` append-only.
8. Ajouter `graph_query_cli` pour chercher claim/evidence/residue.

## Statut

Prototype v1 opérationnel, OAK-safe, dry-run, sans promesse de preuve automatique.
