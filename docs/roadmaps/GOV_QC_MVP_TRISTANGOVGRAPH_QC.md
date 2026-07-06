# TristanGovGraph Québec — MVP Roadmap

Status: A/B — architecture + prototype skeleton
Date: 2026-07-06
Branch: omega-gov-qc-t-mvp

## 1. Objectif MVP

Construire un noyau réutilisable pour transformer les données publiques québécoises en graphe gouvernemental vérifiable : ministères, organismes, municipalités, régions, programmes, contrats, sources, indicateurs et risques.

Le MVP ne prend aucune décision sensible. Il produit uniquement des cartes, signaux, rapports et recommandations explicables.

## 2. Livrable minimal

```text
TristanGovGraph Québec
  - ingestion de sources ouvertes
  - normalisation de noeuds gouvernementaux
  - relations entre entités publiques
  - OAKGate gouvernemental
  - rapports de risques et qualité de données
  - export JSON/Markdown
```

## 3. Phases

### Phase 0 — Stase cognitive / doctrine

- Verrouiller Ω-GOV-QC-T.
- Définir les interdits.
- Définir les gates OAK.
- Créer schéma de noeuds gouvernementaux.
- Créer seed graph minimal.

### Phase 1 — Données ouvertes publiques

- Source registry.
- Ingestion CSV/JSON/API.
- Hash de provenance.
- Normalisation des noms d'organismes.
- Détection de doublons.
- Détection de champs manquants.

### Phase 2 — GovGraph

- Noeuds : ministère, organisme, municipalité, région, programme, contrat, source, indicateur, risque.
- Arêtes : responsable_de, finance, administre, opère_dans, publie, dépend_de, signale_risque, documente.
- Export NetworkX/JSON.
- Rapport topologique : composantes, isolats, dépendances critiques.

### Phase 3 — OAKGate

- LegalGate.
- PrivacyGate.
- SecurityGate.
- FairnessGate.
- ExplainabilityGate.
- HumanAuthorityGate.
- EvidenceGate.
- RobustnessGate.
- UtilityGate.

### Phase 4 — Rapports

- Rapport qualité de données.
- Rapport risques publics.
- Rapport anomalies contractuelles non accusatoires.
- Rapport couverture territoriale.
- Rapport opportunités de services numériques.

### Phase 5 — Produit

- CLI.
- API FastAPI.
- Dashboard web.
- Export municipal.
- Mode SaaS privé.
- Mode audit livré en PDF/Markdown.

## 4. Modules Python proposés

```text
omega_gov_qc_t/
  src/omega_gov_qc_t/
    __init__.py
    gov_graph.py
    oak_gate.py
  schemas/
    gov_node.schema.json
  examples/
    qc_government_seed.json
```

## 5. Statuts OAK

| Statut | Signification |
|---|---|
| A | Implémenté/testé localement |
| B | Doctrine ou architecture claire |
| C | Prototype partiel |
| D | Démontré par benchmark |
| M⁻ | Échec, risque ou anti-pattern à conserver |

## 6. Mémoire négative M⁻ initiale

- Ne jamais appeler une anomalie « fraude » sans enquête humaine.
- Ne jamais utiliser des données personnelles si les données ouvertes suffisent.
- Ne jamais mélanger analyse administrative et ciblage politique.
- Ne jamais rendre une décision de prestation/service par IA seule.
- Ne jamais publier un graphe contenant des personnes privées identifiables.
- Ne jamais ignorer la date, la source et la licence d'un jeu de données.

## 7. Critères de succès

Le MVP réussit si :

- chaque noeud a une source ou une justification ;
- chaque rapport distingue signal, hypothèse, preuve et recommandation ;
- les gates OAK peuvent bloquer un déploiement ;
- l'export est réutilisable par municipalités, chercheurs ou auditeurs ;
- aucune donnée personnelle sensible n'est requise pour la démonstration ;
- le système peut être élargi par ministère ou municipalité sans réécrire le noyau.
