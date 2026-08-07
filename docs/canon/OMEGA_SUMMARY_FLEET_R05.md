# Ω-SUMMARY-FRACTAL-T∞ — Canon R0.5 Fleet

## Statut

Extension canonique R0.5 de l'observatoire R0.4. Elle porte sur la fédération de résumés GitHub, la confidentialité des inventaires privés, la continuité d'identité et l'interrogation agrégée. Elle n'ajoute aucune autorité scientifique, juridique, IP ou commerciale aux métriques structurelles.

## Objets canoniques

### FleetPublic

Projection organisationnelle pseudonymisée :

```text
FleetPublic = {
  fleet_id,
  fingerprint,
  repo_tokens,
  aggregate_structural_metrics,
  privacy_invariants
}
```

### FleetHistory

```text
F_0 -> F_1 -> ... -> F_n
```

avec :

```text
h_n = SHA256(h_{n-1} || canonical(F_n))
```

### AliasApproval

```text
AliasApproval(source, target, evidence_ref, approved_by)
```

Une proposition issue d'Identity Continuity n'est jamais une approbation.

### QueryPlan

```text
QueryPlan = Seed + AND + OR + NOT + GroupBy + Aggregates + Sort + Limit
```

## Invariants obligatoires

1. **No raw private inventory by default** — Fleet public ne sérialise ni noms de dépôts ni noms de systèmes.
2. **No salt serialization** — le sel HMAC reste runtime-only.
3. **Stable fleet scope** — ajouter/retirer un dépôt change le fingerprint, pas le `fleet_id`, tant que le sel reste identique.
4. **Salt rotation is explicit discontinuity** — changer le sel change volontairement l'identité pseudonymisée de flotte.
5. **No implicit alias approval** — Identity Continuity produit seulement des candidats `review_required`.
6. **Alias registry is hash-chained** — toute approbation garde preuve, approbateur, timestamp et intégrité.
7. **No alias cycles** — les graphes d'alias cycliques sont refusés.
8. **No query authority laundering** — filtrer, grouper ou agréger des métriques ne crée pas de vérité scientifique.
9. **Read-only reusable workflow** — `contents: read` demeure la permission GitHub par défaut.
10. **Fleet secret is opt-in** — absence de secret = absence de Fleet, jamais fallback faible.

## Non-claims

R0.5 ne prétend pas :

- identifier juridiquement un dépôt;
- garantir l'anonymat contre un adversaire disposant du sel;
- prouver que deux systèmes renommés sont identiques;
- mesurer la qualité scientifique à partir de `C_struct`;
- mesurer PMF/revenu/IP à partir du dashboard;
- fusionner automatiquement des systèmes;
- déplacer ou renommer automatiquement des fichiers/dépôts;
- publier l'inventaire privé d'une organisation.

## Mantras

```text
OBSERVE MORE != CLAIM MORE
AGGREGATE MORE != EXPOSE MORE
CANDIDATE != APPROVAL
STRUCTURE != TRUTH
```
