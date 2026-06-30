# Ω-HOSTING-T Infra Runbook

Ce dossier transforme la doctrine `docs/OMEGA_HOSTING_T.md` en artefacts de déploiement prudents.

## Objectif

Publier les systèmes Tristan rapidement tout en séparant :

- site public ;
- code source ;
- automatisations ;
- données ;
- secrets ;
- actifs brevetables ;
- logs OAK.

## Composition

```text
infra/omega-hosting/
├── README.md
├── omega_hosting_manifest.yaml
├── docker-compose.n8n.yml
├── env.example
└── oak_deployment_checklist.md
```

## Décision d'usage

Utiliser Hostinger pour :

- pages publiques ;
- domaine et courriels ;
- WordPress/site statique ;
- VPS n8n ;
- webhooks légers ;
- APIs simples.

Ne pas utiliser Hostinger comme :

- coffre unique de secrets ;
- serveur GPU ;
- base de données critique unique ;
- source de vérité du code ;
- moteur d'agents autonomes sensibles ;
- stockage de données personnelles non chiffrées.

## Déploiement recommandé

### 1. Public Layer

- Hostinger Web/Cloud ou Vercel/Cloudflare.
- Contenu : pages marketing, docs publiques, blog.
- Source : GitHub.
- Secrets : aucun dans le front-end.

### 2. Automation Layer

- VPS séparé.
- `docker-compose.n8n.yml` comme squelette.
- `.env` réel sur le serveur seulement.
- Backups + firewall + HTTPS.

### 3. Data Layer

- Supabase/Postgres dédié.
- Pas de données critiques dans fichiers plats publics.
- Backups externes.

### 4. OAK Layer

Avant chaque action :

```text
classification → risque → approbation → exécution → preuve → rollback
```

## Commandes conceptuelles

Aucune commande ne doit être copiée aveuglément en production. Ce dossier fournit des squelettes. Les valeurs réelles doivent être validées dans un environnement contrôlé.

```bash
# exemple local seulement
docker compose -f docker-compose.n8n.yml --env-file .env up -d
```

## Variables critiques

- `N8N_ENCRYPTION_KEY` : ne jamais perdre, ne jamais commiter.
- `POSTGRES_PASSWORD` : secret fort, rotation si fuite.
- `N8N_BASIC_AUTH_PASSWORD` : secret fort.
- `WEBHOOK_URL` : doit pointer vers HTTPS.

## Stratégie zéro-touch prudente

Zéro-touch ne veut pas dire zéro contrôle. Pour Tristan :

- génération automatique : oui ;
- PR automatique : oui ;
- draft email automatique : oui ;
- envoi réel sensible : approbation explicite ;
- publication IP sensible : analyse IP avant ;
- action légale/financière/santé : humain obligatoire.

## Prochaine amélioration

Créer un workflow GitHub Actions qui :

1. vérifie qu'aucun secret n'est commité ;
2. valide le YAML du manifeste ;
3. lance `oak_hosting_gate.py` ;
4. publie un rapport de décision en commentaire PR.
