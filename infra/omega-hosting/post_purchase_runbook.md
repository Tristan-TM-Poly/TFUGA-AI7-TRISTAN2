# Ω-HOSTING-T — Runbook post-achat Hostinger KVM 8

Ce runbook commence **après** achat du VPS. Il ne demande jamais de publier des secrets dans GitHub ou dans un commentaire public.

## 0. Objectif

Transformer le VPS KVM 8 en serveur d'automatisation prudent :

```text
Ubuntu 24.04 LTS → firewall → Docker → reverse proxy HTTPS → n8n → backups → OAK logs
```

## 1. Paramètres recommandés à l'achat

| Paramètre | Valeur recommandée |
|---|---|
| Plan | KVM 8 |
| OS | Ubuntu 24.04 LTS |
| Nom | omega-vps-01 |
| Rôle | n8n, webhooks, API légère, agents légers |
| Données critiques | plutôt Supabase/Postgres externe ou backups testés |
| IA lourde | cloud GPU/local, pas ce VPS |

## 2. Informations non sensibles à noter

Après achat, noter localement :

- IP publique ;
- région/datacenter ;
- OS exact ;
- domaine ou sous-domaine choisi ;
- méthode d'accès SSH ;
- date d'achat ;
- prix de renouvellement ;
- politique de sauvegarde/snapshot.

Ne jamais coller dans GitHub ou le chat : mots de passe, clés privées, jetons, cookies, codes 2FA, informations de paiement.

## 3. Première connexion

Actions humaines requises :

1. ouvrir la console Hostinger ;
2. confirmer que l'OS est Ubuntu 24.04 LTS ;
3. créer ou sélectionner une clé SSH ;
4. se connecter au VPS ;
5. créer un utilisateur admin non-root si nécessaire.

## 4. Bootstrap serveur

Le fichier `bootstrap_ubuntu_24_04.sh` prépare la base :

- mise à jour système ;
- paquets essentiels ;
- Docker ;
- firewall ;
- fail2ban ;
- unattended-upgrades ;
- répertoires `/opt/omega-hosting`.

Avant exécution : lire le script. Il est volontairement conservateur.

## 5. DNS

Créer un sous-domaine dédié, par exemple :

```text
n8n.ton-domaine.example → A → IP_DU_VPS
```

Attendre la propagation DNS avant HTTPS.

## 6. Déploiement n8n prudent

Architecture :

```text
Internet → HTTPS reverse proxy → localhost:5678 → n8n → Postgres Docker volume
```

Le compose existant lie n8n sur `127.0.0.1`, donc n8n n'est pas exposé directement sans reverse proxy.

## 7. Backups minimaux

Obligatoire avant production :

- snapshot VPS avant modifications majeures ;
- export Postgres régulier ;
- copie externe chiffrée ;
- test de restauration ;
- sauvegarde hors dépôt de la clé de chiffrement n8n.

## 8. OAK actions sensibles

n8n peut lire, classer, créer des brouillons et créer des issues. Par défaut, il ne doit pas :

- envoyer des emails sans approbation ;
- publier publiquement sans approbation ;
- modifier des permissions ;
- supprimer des données ;
- traiter des paiements ;
- prendre un engagement légal ;
- exposer de l'IP confidentielle.

## 9. Recette rollback

Si problème :

1. désactiver le workflow n8n concerné ;
2. arrêter le compose ;
3. restaurer le dernier snapshot ou dump ;
4. révoquer/rotater les accès potentiellement exposés ;
5. documenter l'incident dans M⁻ ;
6. redéployer seulement après OAK.

## 10. Feu vert final d'achat

Le feu vert existe seulement si :

- le workflow `Ω-HOSTING-T OAK` est vert ;
- le workflow `Ω-HOSTING-T Prebuy` est vert ;
- la PR de préparation est mergeable ou déjà mergée ;
- ce runbook existe ;
- le bootstrap existe ;
- aucun secret réel n'est dans Git ;
- les actions sensibles sont limitées par approbation humaine.
