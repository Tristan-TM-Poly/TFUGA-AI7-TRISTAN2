# Ω-HOSTING-T — OAK Deployment Checklist

## 1. Classification

- [ ] L'actif est classé avant publication.
- [ ] Le statut est `public_open` ou `public_marketing` si publié.
- [ ] Les détails brevetables/confidentiels sont retirés ou déplacés en dépôt privé.
- [ ] Les données personnelles sont absentes, minimisées ou chiffrées.

## 2. Sécurité

- [ ] Aucun fichier de configuration réel contenant des valeurs privées n'est commité.
- [ ] Les clés et jetons restent dans le gestionnaire de secrets ou sur le serveur.
- [ ] Le VPS n'expose que les ports nécessaires.
- [ ] HTTPS est obligatoire pour toute interface connectée.
- [ ] Les comptes admin utilisent des valeurs uniques et fortes.

## 3. Données

- [ ] La base critique n'est pas hébergée sur un simple hébergement partagé.
- [ ] Les sauvegardes sont testées.
- [ ] Les journaux ne gardent pas plus que nécessaire.
- [ ] Les workflows qui manipulent des emails, fichiers ou contacts sont en mode brouillon ou approbation.

## 4. Actions externes

- [ ] Pas d'envoi automatisé massif.
- [ ] Pas d'engagement légal/financier sans validation humaine.
- [ ] Pas de publication publique sensible sans revue OAK/IP.
- [ ] Chaque action possède une preuve et une recette de rollback.

## 5. Déploiement

- [ ] Source GitHub propre.
- [ ] Branche dédiée.
- [ ] PR lisible.
- [ ] Preview vérifiée.
- [ ] Rollback par revert ou redéploiement précédent.
- [ ] Incident log prêt.

## 6. Score final

| Critère | Score 0-2 |
|---|---:|
| Exposition minimale |  |
| Secrets protégés |  |
| IP protégée |  |
| Données protégées |  |
| Rollback possible |  |
| Preuve de déploiement |  |
| Approbation humaine si sensible |  |
| Coût et maintenance raisonnables |  |

**Décision :**

- `0-7` : bloquer.
- `8-11` : corriger avant publication.
- `12-16` : déploiement prudent possible.
