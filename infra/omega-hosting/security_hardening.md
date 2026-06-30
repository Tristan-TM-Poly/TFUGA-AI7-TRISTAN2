# Ω-HOSTING-T — durcissement extrême avant achat

But : préparer le KVM 8 comme serveur d'automatisation sérieux, sans transformer le VPS en boîte noire dangereuse.

## 1. Politique serveur

| Domaine | Règle |
|---|---|
| Accès | SSH par clé, pas de connexion interactive inutile |
| Ports publics | 80/443, SSH restreint autant que possible |
| Services | Docker/Caddy/n8n/Postgres seulement au départ |
| Données | minimisation, backups, rétention courte |
| Actions externes | approbation humaine obligatoire |
| Déploiements | PR GitHub + OAK + rollback |
| Logs | utiles mais minimisés |

## 2. Durcissement réseau

- UFW actif.
- Ports 80/443 ouverts uniquement pour le reverse proxy.
- n8n non exposé directement sur l'interface publique.
- Postgres jamais exposé publiquement.
- Docker network interne pour n8n/Postgres.
- DNS séparé pour `n8n.<domaine>`.

## 3. Durcissement Docker

- Un compose par rôle.
- Volumes nommés, pas de bind-mount massif.
- Pas de montage du socket Docker dans n8n.
- Pas de mode privileged.
- Redémarrage `unless-stopped`, pas d'auto-update aveugle.
- Mise à jour manuelle sous OAK.

## 4. Durcissement n8n

- HTTPS obligatoire.
- Clé de chiffrement stable conservée hors Git.
- Exécutions prunées.
- Workflows sensibles désactivés par défaut.
- Draft-only pour emails/messages.
- Webhooks publics séparés des workflows internes.
- Credentials n8n minimaux et révocables.

## 5. Backups extrêmes raisonnables

Stratégie 3-2-1 légère :

1. dump local court terme ;
2. snapshot VPS avant changement majeur ;
3. copie externe chiffrée ;
4. test restore mensuel ;
5. hash SHA256 de chaque dump ;
6. journal OAK de chaque restauration.

## 6. Incident response

Si doute :

```text
stop workflow → stop compose → snapshot → rotate access → restore/test → M⁻ incident → PR corrective
```

## 7. Conditions de feu vert achat

Le feu vert reste conditionnel :

- workflows GitHub verts ;
- runbook lisible ;
- bootstrap non destructif ;
- aucune donnée privée dans Git ;
- aucune action externe autonome ;
- budget/renouvellement vérifié ;
- décision d'achat humaine.
