# Ω-GOV-QC-T++ — Product Factory

Status: B / Product architecture
Date: 2026-07-06
Branch: omega-gov-qc-t-mvp

## 0. Mission

Convertir Ω-GOV-QC-T en usine de produits GovTech OAK-safe. Chaque produit doit produire de la valeur publique mesurable sans remplacer les autorités humaines, les processus légaux ou les mécanismes de contestation.

## 1. Familles de produits

### A. CitizenFlow

- assistant de navigation administrative ;
- checklists de démarches ;
- rappel de documents manquants ;
- vulgarisation en langage clair ;
- escalade vers humains lorsque le contexte est sensible.

### B. Municipalité-OAK

- rapport municipal automatisé ;
- qualité des données publiques ;
- carte des services et infrastructures ;
- priorités de correction ;
- registre M- des problèmes récurrents.

### C. OpenData-CVCD

- ingestion de fichiers CSV/JSON/API ;
- normalisation ;
- détection de champs manquants ;
- provenance et hash ;
- exports graph/JSON/Markdown.

### D. BudgetTrace

- budget vers programme ;
- programme vers service ;
- service vers résultat ;
- comparaison temporelle ;
- rapport d'écarts et limites.

### E. Integrity Signals

- signaux administratifs à vérifier ;
- anomalies statistiques non concluantes ;
- contre-explications ;
- dossier de revue ;
- aucun verdict automatique.

### F. Privacy-OAK

- registre de flux de données ;
- minimisation ;
- classification ;
- revue des usages ;
- gate avant déploiement.

### G. CyberShield-QC

- inventaire d'actifs ;
- dépendances ;
- risques de configuration ;
- suivi des correctifs ;
- mémoire d'incidents M-.

### H. JusticeAccess-OAK

- explication de parcours ;
- résumé documentaire ;
- échéances ;
- pièces à rassembler ;
- aucune décision juridique finale.

## 2. Structure produit commune

Chaque produit doit contenir :

```text
ProductCard
  name
  public_mission
  users
  input_data
  output_type
  human_authority_level
  risk_level
  oak_gates
  metrics
  m_minus
  monetization_path
```

## 3. Niveaux de maturité

| Niveau | Nom | Critère |
|---|---|---|
| P0 | Doctrine | idée structurée, limites et risques |
| P1 | Skeleton | package, schéma et tests minimum |
| P2 | Demo | exemple reproductible avec données publiques |
| P3 | Pilot | cas réel avec partenaire et revue humaine |
| P4 | Product | SaaS/API/dashboard documenté |
| P5 | Platform | plusieurs produits interopérables |

## 4. Business model prudent

Hypothèses à tester :

- rapports ponctuels pour municipalités ;
- audit de qualité de données ;
- conformité et registre de sources ;
- tableau de bord hébergé ;
- intégration API ;
- formation OAK/IA responsable ;
- support technique.

Aucune hypothèse de revenu n'est canonisée sans validation marché.

## 5. OAK de commercialisation

Avant vendre ou déployer :

1. preuve que le produit ne requiert pas de données sensibles pour la démo ;
2. description claire des limites ;
3. revue des termes de service et licences de données ;
4. métrique de valeur mesurable ;
5. processus de correction des erreurs ;
6. personne responsable identifiée ;
7. documentation des risques.

## 6. Prochain build recommandé

```text
TristanGovGraph Québec v0.2
  + SourceRegistry
  + EvidenceGraph
  + RiskTensor
  + MarkdownReportFactory
  + municipal demo report
```
