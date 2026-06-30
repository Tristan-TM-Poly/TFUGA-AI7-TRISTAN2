# Ω-HOSTING-T — procédure de restauration n8n/Postgres

Cette procédure est volontairement séparée du script de backup pour éviter une restauration accidentelle.

## Quand utiliser

- corruption de données ;
- migration VPS ;
- test de restauration ;
- retour arrière après incident.

## Préconditions

- dump Postgres valide ;
- empreinte SHA256 vérifiée ;
- n8n arrêté ou fenêtre de maintenance ;
- décision OAK consignée ;
- snapshot VPS récent avant restauration.

## Procédure conceptuelle

1. Mettre n8n en maintenance.
2. Créer un backup immédiat de l'état courant, même mauvais.
3. Vérifier le fichier de dump choisi.
4. Restaurer dans une base temporaire si possible.
5. Tester login, workflows, credentials chiffrés et webhooks.
6. Basculer seulement si les tests passent.
7. Documenter l'incident dans `oak-ledger` et M⁻.

## Commande type à adapter

```bash
# Exemple à adapter sur VPS, après revue humaine.
# docker compose exec -T postgres pg_restore -U n8n -d n8n --clean --if-exists < backup.dump
```

## OAK

Ne jamais restaurer aveuglément en production. Une restauration écrase potentiellement des données plus récentes.
