# Ω-SYNERGY-N-T∞ R2 — Threat model

## Actifs protégés

- provenance des mesures;
- intégrité du treillis de sous-ensembles;
- séparation des contextes;
- frontières d'autorité;
- résultats négatifs M−;
- reproductibilité des bundles;
- dépôts et données analysés.

## Menaces

### Treillis incomplet présenté comme exact

Mitigation : validation obligatoire de toutes les faces avant inversion exacte.

### Similarité présentée comme interaction

Mitigation : les moteurs de recherche produisent seulement des candidats heuristiques.

### Score compensant une gate absente

Mitigation : gates booléennes évaluées avant le score.

### Plan fractionnaire interprété sans alias

Mitigation : groupes d'alias inclus dans le contrat du plan.

### Mélange de contextes

Mitigation : décomposition rejetée si les `context_id` diffèrent.

### Effets corrélés sous erreur indépendante

Mitigation : limitation explicite; future prise en charge de covariance séparée.

### Explosion combinatoire

Mitigation : caps de plan complet, beam width, ordre maximal, budget et stop gate.

### Génération récursive incontrôlée

Mitigation : budget fini, gouverneur et arrêt obligatoires.

### Contamination des preuves

Mitigation : provenance, ledger append-only et distinction indépendance/dépendance.

### Fausse sécurité cryptographique

Mitigation : le manifeste indique que l'intégrité n'est pas la vérité.

### Fusion ou publication automatique

Mitigation : `automatic_merge_allowed=false`, `automatic_publication_allowed=false`, permissions CI en lecture seule.

### Données sensibles

R2 n'a besoin d'aucun secret, credential, donnée bancaire, dossier médical ou identifiant personnel.
Les connecteurs et acquisitions externes doivent rester en dehors du noyau exact et passer par leurs propres autorisations.

## Autorité maximale

```yaml
maximum_authority: review_only
human_review_required: true
automatic_merge_allowed: false
automatic_publication_allowed: false
scientific_proof_claimed: false
causal_validation_claimed: false
```
