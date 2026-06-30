# Ω-HOSTING-T — Infrastructure publique légère de Tristan

**Statut :** doctrine d'architecture, blueprint de déploiement et garde-fou OAK pour publier les systèmes Tristan sans mélanger vitrine, code, données privées, agents et calcul lourd.

## 0. Résumé exécutif

Ω-HOSTING-T transforme l'hébergement web en couche d'action contrôlée : publier vite, automatiser léger, garder les secrets privés, et router chaque composant vers l'infrastructure adaptée.

La règle mère :

```text
GitHub = cerveau du code
Hostinger = façade publique + petits services + VPS léger
Vercel/Cloudflare = apps web modernes rapides
Supabase/Postgres = données structurées
Cloud GPU externe = IA lourde / simulations lourdes
OAK = garde-fou permission, risque, rollback, preuve
```

Hostinger est utile pour les landing pages, domaines, courriels, WordPress, petits sites, VPS n8n, webhooks, bots légers et prototypes de démonstration. Hostinger ne doit pas devenir la source de vérité du code, la base unique des données sensibles, ni le moteur principal des agents AIT lourds.

## 1. But de la branche

Créer une architecture déployable pour :

1. exposer proprement les théories, prototypes et actifs de Tristan ;
2. convertir les systèmes Ω en pages, docs, APIs et dashboards ;
3. héberger des automatisations légères avec n8n / webhooks / cron ;
4. séparer strictement public, privé, brevetable, expérimental et critique ;
5. préparer une trajectoire revenus / publications / partenaires sans fuite IP ;
6. garder une trace OAK de chaque action externe.

## 2. Ontologie d'infrastructure

### 2.1 Couches canoniques

| Couche | Rôle | Infrastructure préférée | Niveau de risque |
|---|---|---|---|
| Public Layer | Site, blog, landing pages, docs publiques | Hostinger Web/Cloud, Vercel, Cloudflare Pages | Bas à moyen |
| Code Layer | Source de vérité du code | GitHub | Moyen si public, élevé si secrets |
| Automation Layer | n8n, webhooks, petits agents | Hostinger VPS, Railway, Render | Moyen à élevé |
| Data Layer | Postgres, Auth, Storage, Vector | Supabase/Postgres dédié | Élevé |
| Compute Layer | Simulations, IA lourde, GPU | Cloud GPU spécialisé/local | Élevé |
| OAK Layer | permission, secrets, logs, rollback | GitHub + DB + append-only ledger | Critique |
| IP Layer | brevetable, secret commercial, publication | dépôt privé + coffre IP + analyse humaine | Critique |

### 2.2 Principe de moindre exposition

Tout actif passe dans ce filtre :

```text
Objet X → classification IP/privacy → choix infra → garde OAK → déploiement → preuve → rollback possible
```

Classification minimale :

- `public_open` : peut être publié.
- `public_marketing` : peut être présenté sans détails critiques.
- `confidential_ip` : brevetable ou secret commercial ; ne pas publier.
- `private_personal` : données personnelles ; chiffrer et minimiser.
- `regulated_sensitive` : santé, finances, juridique, sécurité ; humain obligatoire.
- `dangerous_or_dual_use` : sécurité physique/cyber/laser/lab ; blocage ou revue stricte.

## 3. Architecture cible

```text
Ω-TRISTAN-INFRA
│
├── 01_public_site
│   ├── tristan.systems
│   ├── pages Ω-théories
│   ├── blog / publications
│   ├── pages produits
│   └── formulaires contact
│
├── 02_code_brain
│   ├── GitHub repos
│   ├── issues / PR / releases
│   ├── CI/CD
│   └── documentation technique
│
├── 03_automation_vps
│   ├── n8n
│   ├── webhooks
│   ├── cron jobs
│   ├── API légères
│   └── agents AIT légers
│
├── 04_data_core
│   ├── Postgres
│   ├── Auth
│   ├── Storage
│   ├── Vector embeddings
│   └── backups
│
├── 05_app_runtime
│   ├── dashboards
│   ├── Next.js / React
│   ├── API serverless
│   └── preview deployments
│
└── 06_oak_control
    ├── secrets policy
    ├── risk gates
    ├── approval queue
    ├── audit ledger
    ├── incident register
    └── rollback recipes
```

## 4. Matrice Hostinger pour les systèmes Tristan

| Cas d'usage | Hostinger Web | Hostinger Cloud | Hostinger VPS | Meilleur choix |
|---|---:|---:|---:|---|
| Portfolio / vitrine | Oui | Oui | Inutile | Web ou Cloud |
| Blog WordPress | Oui | Oui | Possible | Web Business/Cloud |
| Pages produits | Oui | Oui | Inutile | Web/Cloud |
| Documentation statique | Oui | Oui | Possible | Cloudflare/Vercel/Hostinger |
| n8n léger | Non recommandé | Possible | Oui | VPS |
| Agents webhooks | Non | Possible | Oui | VPS |
| API Python légère | Non | Possible | Oui | VPS/Render/Railway |
| Dashboard Next.js | Moyen | Moyen | Possible | Vercel/Cloudflare |
| Données critiques | Non | Moyen | Moyen | Supabase/Postgres dédié |
| IA lourde / GPU | Non | Non | Non | Cloud GPU |
| Secret IP complet | Non | Non | Non seul | dépôt privé + coffre + OAK |

## 5. Modules Ω-HOSTING-T

### 5.1 Ω-HOSTING-GATE

Décide si un composant peut aller sur Hostinger.

Entrées :

- type de composant ;
- niveau de données ;
- besoin CPU/RAM/GPU ;
- exposition publique ;
- besoin de disponibilité ;
- présence de secrets ;
- statut IP ;
- niveau d'autonomie agentique ;
- capacité de rollback.

Sorties :

- `allow_hostinger_web`
- `allow_hostinger_vps`
- `prefer_external_cloud`
- `block_until_review`
- score OAK
- raisons
- actions minimales.

### 5.2 Ω-DOMAIN-MAP

Carte des domaines possibles :

```text
tristan.systems         → portail global
omega-tristan.com      → théories Ω
tristanlabs.ca         → crédibilité Québec/Canada
ait-tristan.dev        → agents et prototypes
tristan.energy         → énergie / matériaux
tristan.pub            → publications publiques
```

Règle IP : les noms publics ne doivent pas révéler une invention brevetable non protégée.

### 5.3 Ω-DEPLOY-RAIL

Rail de déploiement standard :

```text
idée → issue GitHub → branche → fichiers → OAK check → PR → preview → merge → deploy → postmortem léger
```

### 5.4 Ω-SECRETS-GATE

Secrets interdits dans le dépôt et dans le front-end :

- clés OpenAI / Anthropic / GitHub / Supabase ;
- tokens SMTP ;
- mots de passe DB ;
- clés SSH ;
- cookies ;
- fichiers `.env` réels ;
- dumps de données ;
- documents personnels non filtrés.

Autorisé : `.env.example` sans secrets réels.

### 5.5 Ω-OAK-LEDGER

Chaque action externe produit :

```yaml
action_id: HOSTING-YYYYMMDD-001
intent: publier une landing page Ω
asset_class: public_marketing
risk_level: medium
human_approval: required_if_email_or_payment
rollback: revert commit + redeploy previous version
proof: PR link + deployment URL + checks
residual_risk: IP leakage if page too detailed
```

## 6. Profils de déploiement

### Profil A — Vitrine minimale

Pour publier vite :

- Hostinger Web Business/Cloud ;
- domaine ;
- email professionnel ;
- blog ou site statique ;
- GitHub pour le code ;
- pages publiques seulement.

Risque : faible.

### Profil B — Automation légère

Pour n8n + webhooks :

- Hostinger VPS ;
- Docker Compose ;
- reverse proxy ;
- SSL ;
- sauvegardes ;
- firewall ;
- `.env` local ;
- logs minimisés.

Risque : moyen à élevé selon les intégrations.

### Profil C — Jarvis public contrôlé

Pour assistant personnel/corporatif léger :

- site public sur Hostinger/Vercel ;
- backend/API séparé ;
- Supabase pour données ;
- n8n pour orchestration ;
- human-in-the-loop pour emails, paiements, messages, contrats ;
- OAK ledger obligatoire.

Risque : élevé.

### Profil D — Recherche lourde

Pour simulations, IA lourde, Rosette PDF, calcul numérique :

- pas Hostinger comme compute principal ;
- GitHub + cloud GPU/local ;
- données privées chiffrées ;
- artefacts publics filtrés.

Risque : élevé à critique.

## 7. Runbook de déploiement n8n VPS

1. Créer VPS dédié, pas mélangé au site public.
2. Activer firewall : ports 22, 80, 443 seulement au départ.
3. Utiliser Docker Compose avec volume persistant.
4. Mettre n8n derrière HTTPS.
5. Configurer `N8N_ENCRYPTION_KEY` une seule fois et la sauvegarder hors dépôt.
6. Désactiver l'exposition publique des workflows sensibles.
7. Créer sauvegarde DB automatique.
8. Journaliser les actions externes sensibles.
9. Tester rollback avant usage réel.
10. Interdire l'envoi automatisé massif sans consentement et validation.

## 8. OAK checklist avant publication

- [ ] L'actif est classé `public_open` ou `public_marketing`.
- [ ] Aucun secret réel dans le code.
- [ ] Aucune donnée personnelle non nécessaire.
- [ ] Aucune invention brevetable révélée sans analyse IP.
- [ ] Les pages ne promettent pas de performance non validée.
- [ ] Les limites sont affichées quand requis.
- [ ] Le rollback est possible.
- [ ] Les logs ne collectent pas plus que nécessaire.
- [ ] Les formulaires ont consentement et usage clair.
- [ ] Les agents externes ont un garde humain pour actions sensibles.

## 9. Anti-patterns M⁻

| Anti-pattern | Pourquoi c'est dangereux | Correction |
|---|---|---|
| Tout mettre sur un seul hébergement | panne, fuite, dette technique | séparer couches |
| Mettre `.env` dans GitHub | fuite secrets | `.env.example` seulement |
| Publier théorie brevetable trop tôt | perte potentielle IP | IP gate avant publication |
| Agents qui envoient sans validation | réputation/légal | approval queue |
| WordPress surchargé de plugins | vulnérabilités | plugins minimaux |
| Pas de backups | perte de données | snapshots + export externe |
| Hostinger comme GPU | mauvais fit | cloud GPU spécialisé |
| Base de données critique sur site web simple | fragilité | Supabase/Postgres dédié |

## 10. Roadmap maximale

### Sprint 1 — Base publique

- landing page Tristan Systems ;
- page `Théories Ω` ;
- page `Prototypes` ;
- page `Contact / collaborations` ;
- README infra ;
- OAK checklist.

### Sprint 2 — Automation

- VPS n8n ;
- webhooks entrants ;
- formulaire → GitHub issue ;
- formulaire → Gmail draft, pas send automatique ;
- backup scripts ;
- incident log.

### Sprint 3 — Données et dashboards

- Supabase project ;
- tables `assets`, `actions`, `oak_checks`, `deployments`; 
- dashboard interne ;
- vector index pour docs publiques seulement.

### Sprint 4 — Revenus/IP

- pages produits ;
- lead capture conforme ;
- pipeline partenaires ;
- IP vault privé ;
- publication gate ;
- analytics minimalistes.

### Sprint 5 — AIT-Jarvis contrôlé

- agents lecture seule ;
- actions draft-only ;
- approvals ;
- rollback ;
- audit ledger ;
- red team OAK.

## 11. Forme canonique

```text
X = actif/prototype/théorie/action
C = classification publique/privée/IP/sensible
I = infrastructure candidate
R = risque résiduel
P = preuve de déploiement

Ω-HOSTING-T(X) = deploy(I*) seulement si OAK(X,C,I,R,P) ≥ seuil
```

Le système ne cherche pas l'hébergement le moins cher. Il cherche le meilleur compromis entre vitesse, coût, sécurité, maintenabilité, propriété intellectuelle, preuve et rollback.

## 12. Décision par défaut

Pour l'écosystème Tristan :

```text
Hostinger = oui pour publier et automatiser léger.
Hostinger = non comme cerveau complet, coffre secret, GPU ou base critique unique.
```
