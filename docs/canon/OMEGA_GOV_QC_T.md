# Ω-GOV-QC-T — Systèmes gouvernementaux québécois de Tristan

Status: B / Doctrine + MVP design
Date: 2026-07-06
Owner: Tristan-TM-Poly
Branch: omega-gov-qc-t-mvp

## 0. Phrase-mère

Le gouvernement québécois peut être représenté comme un hypergraphe vivant de missions publiques, lois, organismes, ministères, municipalités, services, programmes, budgets, contrats, données ouvertes, risques, plaintes, décisions et résultats mesurables.

```text
GOV_QC = HGFM(
  missions,
  lois,
  ministères,
  organismes,
  municipalités,
  programmes,
  contrats,
  budgets,
  données,
  citoyens,
  risques,
  décisions,
  preuves,
  impacts
)
```

Le but de Ω-GOV-QC-T n'est pas de remplacer l'autorité publique. Le but est de construire des systèmes qui rendent les services publics plus rapides, plus explicables, plus sécuritaires, plus équitables, plus vérifiables et plus auditables.

## 1. Règle OAK absolue

Toute sortie gouvernementale produite par le système est classée comme l'une des catégories suivantes :

1. **Signal** — indice, anomalie, tendance ou élément de triage.
2. **Hypothèse** — interprétation possible à vérifier.
3. **Preuve structurée** — élément traçable avec source, date, provenance et incertitude.
4. **Recommandation** — action suggérée, explicable et révisable.
5. **Décision humaine** — action finale prise par une autorité compétente.

Règle stricte :

```text
Signal ≠ Preuve ≠ Verdict ≠ Décision publique finale
```

Aucune décision sensible concernant droits, santé, justice, prestations, police, fiscalité, immigration, école, emploi ou réputation ne doit être entièrement automatisée.

## 2. Modules maîtres

### Ω-CITIZEN-T — Citoyen et guichet public

Assistant de navigation administrative : démarches, formulaires, pièces manquantes, échéances, vulgarisation, accessibilité et suivi.

### Ω-MINISTRYGRAPH-T — Graphe ministères/organismes

Cartographie des missions, programmes, lois, budgets, données, indicateurs, responsabilités, dépendances et résidus.

### Ω-OPEN-DATA-CVCD-T — Données ouvertes augmentées

Ingestion de données publiques, normalisation, détection de trous, doublons, incohérences, schémas, provenance et API.

### Ω-MUNICIPAL-T — Municipalités, MRC et régions

Hypergraphe territorial : infrastructures, routes, eau, logement, risques climatiques, subventions, indicateurs, priorisation.

### Ω-PROCUREMENT-INTEGRITY-T — Marchés publics et intégrité

Analyse des contrats, appels d'offres, fournisseurs, variations de prix, délais, avenants, dépendances, anomalies et signaux de collusion potentielle.

### Ω-HEALTH-QC-T — Santé et services sociaux

Prévision de demande, flux, délais, ressources, trajectoires anonymisées, goulots, rapports. Jamais diagnostic autonome.

### Ω-EDU-QC-T — Éducation et apprentissage public

Réussite, soutien aux enseignants, plans d'aide, IA pédagogique, risques de décrochage avec garde-fous, équité et explicabilité.

### Ω-JUSTICE-ADMIN-T — Justice administrative augmentée

Résumé de dossiers, accès aux recours, pièces manquantes, échéanciers, vulgarisation juridique et triage non décisionnel.

### Ω-CYBER-QC-T — Cyberdéfense publique

Registre des actifs, menaces, incidents, dépendances, plans de réponse, audits, M⁻ incident codex et moindre privilège.

### Ω-PRIVACY-LAW25-T — Protection des renseignements personnels

Inventaire de données personnelles, EFVP, anonymisation, conservation, incidents, contrôle d'accès, journalisation et minimisation.

### Ω-CLIMATE-INFRA-T — Climat, infrastructures et territoire

Risques d'inondation, feux, routes, ponts, bâtiments publics, eau, énergie, résilience et scénarios multi-échelles.

### Ω-OVERSIGHT-T — Audit, reddition de comptes et transparence

Rapports OAK, preuves, indicateurs, écarts, conflits, mémoire négative, recommandations auditables.

## 3. Architecture commune

```text
raw_public_data
  -> source_registry
  -> schema_normalizer
  -> provenance_hasher
  -> gov_hypergraph
  -> OAKGate
  -> dashboards / reports / APIs / audit packages
```

Chaque artefact doit conserver :

- source ;
- date d'accès ;
- version ;
- propriétaire ou organisme ;
- licence ou statut d'utilisation ;
- transformation appliquée ;
- résidu ;
- incertitude ;
- statut OAK.

## 4. Gates OAK gouvernementaux

Un module ne peut passer en production que si ces verrous sont explicitement évalués :

1. **LegalGate** — mandat, loi, règlement, contrat, responsabilité.
2. **PrivacyGate** — minimisation, consentement si requis, anonymisation, PRP.
3. **SecurityGate** — accès, secrets, chiffrement, journalisation, incident response.
4. **FairnessGate** — biais, discrimination, impacts disproportionnés.
5. **ExplainabilityGate** — sources, causalité prudente, incertitudes, limites.
6. **HumanAuthorityGate** — humain obligatoire pour décisions sensibles.
7. **EvidenceGate** — traçabilité, reproductibilité, versionnement.
8. **RobustnessGate** — tests, contre-exemples, M⁻, simulations.
9. **UtilityGate** — gain mesuré : temps, coût, qualité, accès, sécurité.

Formule :

```text
DEPLOYABLE = LegalGate
          ∧ PrivacyGate
          ∧ SecurityGate
          ∧ FairnessGate
          ∧ ExplainabilityGate
          ∧ HumanAuthorityGate
          ∧ EvidenceGate
          ∧ RobustnessGate
          ∧ UtilityGate
```

## 5. Produits de compagnie possibles

1. **TristanGovGraph Québec** — hypergraphe des données publiques québécoises.
2. **OAK-Audit Public Contracts** — anomalies et intégrité contractuelle.
3. **Privacy-OAK Public Bodies** — conformité PRP et EFVP.
4. **Municipalité-OAK** — tableau de bord municipal/MRC.
5. **CitizenFlow Québec** — assistant de services publics.
6. **CyberShield-QC** — cybersécurité et cartographie de risques.
7. **ClimateInfra-OAK** — risques climatiques/infrastructures.
8. **JusticeAccess-OAK** — accès à la justice administrative.
9. **Edu-OAK Québec** — IA responsable pour éducation.
10. **Oversight-OAK** — vérification, reddition de comptes et transparence.

## 6. Interdits canoniques

Le système ne doit pas servir à :

- manipulation électorale ;
- microciblage politique ;
- surveillance de citoyens sans base légale ;
- verdict automatique de fraude, crime ou culpabilité ;
- décision automatisée sur droits/prestations/santé/justice ;
- extraction de renseignements personnels sans autorisation ;
- contournement de systèmes gouvernementaux ;
- publication de données sensibles ;
- suppression destructrice ou modification irréversible sans approbation.

## 7. MVP canonique

Premier produit à construire : **TristanGovGraph Québec**.

Objectif : ingérer des sources ouvertes, créer un graphe ministères-organismes-municipalités-programmes-contrats-territoires, détecter incohérences et trous de données, puis générer des rapports OAK explicables.

Ce MVP est choisi parce qu'il maximise l'utilité tout en minimisant les risques : données ouvertes, pas de décision individuelle, haute valeur analytique, forte réutilisabilité et potentiel commercial GovTech.
