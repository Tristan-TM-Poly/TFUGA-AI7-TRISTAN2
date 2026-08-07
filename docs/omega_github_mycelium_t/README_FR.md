# Ω-GITHUB-MYCELIUM-T∞ R0.1

## Orchestrateur récursif multi-dépôts et multi-PR de Tristan

Ω-GITHUB-MYCELIUM-T∞ transforme une intention et un snapshot GitHub autorisé en une campagne probatoire, déterministe et révisable.

```text
intention
→ registre des créations
→ snapshot dépôts + PR
→ hypergraphe global
→ artefacts attendus
→ routage public/privé
→ campagne multi-PR
→ ordre de dépendance
→ OAKGate
→ EvidenceBundle
→ M⁻
→ proposition de synchronisation du canon
```

R0.1 est **read-first** et **dry-run-only**. Il sait lire un portefeuille GitHub, compiler des plans et produire des preuves de planification. Il ne contient aucune autorité implicite de fusion, publication, déploiement, suppression ou modification de permissions.

## Capacités exécutables

### IntentCompiler

Transforme un objectif humain en `IntentContract` déterministe :

- création racine;
- sorties attendues;
- profondeur adaptative;
- dépôts candidats;
- contraintes;
- conditions de réussite;
- autorité distante explicitement absente.

### GitHubReadOnlyScanner

Utilise l’API REST GitHub en lecture seule avec :

- pagination complète des dépôts possédés;
- pagination complète des PR ouvertes;
- HTTPS obligatoire;
- budget maximal par réponse;
- timeout explicite;
- token facultatif depuis l’environnement;
- conservation du digest du corps des PR plutôt que du corps complet;
- aucune méthode d’écriture.

### CreationRegistry

Réutilise les quarante racines de `Ω-DEPTH-T∞` et les relie aux PR observées.

### GlobalRepoGraph

Produit un hypergraphe avec :

- dépôts;
- PR;
- créations;
- relations `hosts_pr`;
- relations `defines_canon`;
- relations `implements_or_documents`;
- dépendances inter-PR déclarées.

Exports : JSON et GraphML.

### ArtifactCompiler

Compile les sorties attendues en contrats d’artefacts :

- théorie;
- graphe système;
- documentation;
- code;
- tests;
- benchmark;
- preuve;
- rapport OAK;
- produit candidat;
- rapport IP.

Chaque artefact précise son chemin, ses dépendances, sa visibilité requise, son risque, son digest et son statut réel `contract_only`.

### RepoRouter

Évalue les dépôts selon :

- cohérence conceptuelle;
- préférence explicite;
- maturité observée;
- permissions;
- statut public ou privé;
- risque de divulgation;
- rôle du dépôt canonique.

Un artefact `private_required` ne peut pas être routé vers un dépôt public sans déclencher un bloqueur OAK.

### PRCampaignPlanner

Regroupe les artefacts par dépôt et produit des PR planifiées :

- branche unique;
- chemins autorisés;
- hypothèse;
- tests attendus;
- dépendances entre PR;
- ordre topologique;
- rollback obligatoire;
- brouillon obligatoire;
- validation humaine obligatoire;
- `permanent_pr_cap: null`.

### CI-OAK

Les gates sont non compensatoires. Une bonne note ne peut jamais compenser :

- une route privée vers un dépôt public;
- une dépendance cyclique;
- un dépôt inconnu;
- une permission d’écriture absente;
- un rollback absent;
- une PR non brouillon;
- une action distante déjà planifiée comme exécutée;
- une autorité de fusion implicite.

### EvidenceVault et mémoire

Le bundle produit conserve :

- digest du snapshot;
- digests des artefacts;
- campagne;
- affirmations autorisées;
- limites;
- résidus;
- M⁻ hash-chaînée;
- proposition de synchronisation du canon.

## Commandes

### Scanner tous les dépôts possédés et leurs PR ouvertes

```bash
omega-mycelium live-scan \
  --owner Tristan-TM-Poly \
  --output generated/omega_github_mycelium_t/live-snapshot.json
```

Le token peut être fourni par `GITHUB_TOKEN`. Le scanner n’effectue aucune mutation.

### Valider un snapshot

```bash
omega-mycelium validate-snapshot \
  generated/omega_github_mycelium_t/live-snapshot.json
```

### Compiler directement un objectif

```bash
omega-mycelium plan \
  --objective "Détecter une divergence entre documentation et code" \
  --root-creation omega-doc-t \
  --snapshot generated/omega_github_mycelium_t/live-snapshot.json \
  --candidate-repository Tristan-TM-Poly/TFUGA-AI7-TRISTAN2 \
  --output-dir generated/omega_github_mycelium_t/omega-doc-campaign
```

### Compiler un contrat d’intention existant

```bash
omega-mycelium compile \
  --intent intent.json \
  --snapshot snapshot.json \
  --output-dir generated/campaign
```

## Artefacts de sortie

```text
intent.json
snapshot-summary.json
creation-registry.jsonl
mycelium-graph.json
mycelium-graph.graphml
artifacts.jsonl
route-decisions.jsonl
campaign.json
oak-report.json
evidence-bundle.json
canon-update-plan.json
m_minus.jsonl
report.md
manifest.json
```

## Snapshot initial

`data/omega_github_mycelium_t/repository_snapshot_2026_08_03.json` conserve les six dépôts possédés observés le 3 août 2026 et un échantillon représentatif de PR. Il est explicitement marqué comme incomplet pour les PR. Une campagne organisationnelle réelle doit utiliser `live-scan` afin d’obtenir la pagination complète au moment de l’exécution.

## Frontières OAK

```text
snapshot GitHub != état éternellement courant
PR ouverte != PR correcte
CI verte != validation scientifique
beaucoup de PR != progrès
route heuristique != décision souveraine
EvidenceBundle != vérité externe
plan de branche != branche créée
plan de PR != PR ouverte
plan de fusion != autorité de fusion
```

## Statut

- architecture : formalisée;
- scanner : implémenté en lecture seule;
- compilation de campagne : implémentée;
- tests : ajoutés, CI exacte en attente;
- mutation distante : absente;
- validation sur tous les dépôts réels : à exécuter avec un snapshot complet et frais;
- fusion automatique : interdite.
