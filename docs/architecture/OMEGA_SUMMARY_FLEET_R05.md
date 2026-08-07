# Ω-SUMMARY-FRACTAL-T∞ R0.5 — Fleet Observatory

## Objet

R0.5 étend l'observatoire R0.4 du niveau dépôt/corpus au niveau **flotte de dépôts**, avec une contrainte supplémentaire : un artefact organisationnel potentiellement partageable ne doit pas révéler par défaut les noms des dépôts privés ni les noms des systèmes qu'ils contiennent.

La chaîne devient :

```text
repository
  -> D0..D9
  -> local history
  -> corpus summary
  -> privacy projection
  -> Fleet public manifest
  -> Fleet hash-chain
  -> Fleet dashboard
```

Le Fleet n'est pas un mécanisme de contrôle des dépôts. C'est une projection read-only des métriques structurelles déjà observées.

## Privacy-first identity

Un dépôt est projeté par :

```text
repo_token = truncate20(HMAC-SHA256(fleet_salt, repository_name))
```

L'identité de flotte est :

```text
fleet_id = truncate20(HMAC-SHA256(fleet_salt, "omega-summary-fleet-v1"))
```

Le `fleet_id` ne dépend pas de la liste courante de dépôts. Ainsi :

- ajouter un dépôt change le fingerprint du snapshot;
- retirer un dépôt change le fingerprint du snapshot;
- la continuité de la flotte reste stable;
- changer le sel rompt volontairement cette continuité.

Le sel :

- est fourni au runtime;
- n'est jamais sérialisé;
- n'a aucun fallback faible;
- n'est jamais codé en dur dans le dépôt;
- doit être traité comme un secret d'observabilité si une stabilité inter-run est désirée.

## FLEET_PUBLIC

`FLEET_PUBLIC.json` contient seulement :

- `fleet_id` pseudonymisé;
- fingerprint structurel du snapshot;
- tokens des dépôts;
- nombre de systèmes;
- distribution `observed/documented/implemented/tested`;
- moyenne de cristallisation structurelle;
- moyenne de dette structurelle;
- compteurs d'attention tests/CI/contrats.

Il ne contient pas :

- nom brut de dépôt;
- nom brut de système;
- chemin absolu;
- URL privée;
- sel HMAC;
- token GitHub;
- secret Actions;
- contenu de fichier.

## Fleet history

`FLEET_HISTORY.json` est une chaîne append-only logique :

```text
entry_hash_n = SHA256(previous_hash || canonical(FLEET_PUBLIC_n))
```

Invariants :

1. même fingerprint => aucune duplication;
2. chaîne invalide => refus d'append;
3. `fleet_id` différent => refus d'append dans la même histoire;
4. aucun nom brut n'est réintroduit dans l'historique;
5. changement de métriques ≠ progrès scientifique.

## Dashboard statique

`FLEET_DASHBOARD.html` est :

- autonome;
- sans dépendance réseau;
- filtrable côté navigateur;
- construit uniquement à partir de la projection publique;
- partageable indépendamment du mapping privé token -> dépôt.

Il n'est pas un système d'autorisation et ne doit jamais devenir une source de vérité d'accès.

## Identity Continuity -> Alias Registry

R0.4 produit des candidats content-addressed :

```text
old_system -> new_system
status = review_required
automatic_rewrite = false
```

R0.5 ajoute deux étapes :

```text
IDENTITY_CONTINUITY
  -> ALIAS_PROPOSALS
  -> explicit approval
  -> ALIAS_REGISTRY
```

`ALIAS_PROPOSALS.json` reste non autoritatif.

`ALIAS_REGISTRY.json` est hash-chaîné et exige :

- source;
- target;
- référence de preuve;
- approbateur explicite;
- timestamp;
- note optionnelle.

Le registre :

- refuse les cycles;
- refuse plusieurs targets approuvés pour une même source;
- déduplique une approbation identique;
- ne consomme jamais automatiquement les candidats R0.4.

Une signature de contenu identique peut résulter d'une copie, d'un fork ou d'un vendoring. Elle ne suffit jamais à approuver un alias.

## Query Plan

R0.5 ajoute une couche déclarative au Query Engine R0.4.

Exemple :

```json
{
  "seed": {"kind": "system"},
  "where": [
    {"field": "structural_crystallization", "op": "gte", "value": 0.6}
  ],
  "any": [
    {"field": "status", "op": "eq", "value": "tested"},
    {"field": "status", "op": "eq", "value": "implemented"}
  ],
  "not": [
    {"field": "path", "op": "contains", "value": "legacy"}
  ],
  "group_by": ["status"],
  "aggregates": [
    {"name": "count", "op": "count"},
    {"name": "mean_c", "op": "mean", "field": "structural_crystallization"}
  ],
  "sort": [{"field": "count", "direction": "desc"}],
  "limit": 100
}
```

Opérateurs :

- `eq`, `ne`;
- `gt`, `gte`, `lt`, `lte`;
- `contains`;
- `in`;
- `exists`.

Agrégations :

- `count`;
- `sum`;
- `mean`;
- `min`;
- `max`.

Les plans interrogent les métadonnées structurelles; une agrégation ne transforme jamais ces métadonnées en causalité ou en vérité scientifique.

## CLI

```bash
# Fleet public à partir d'un corpus/résumé/index
export OMEGA_FLEET_SALT='...runtime secret...'
omega-summary fleet CORPUS_SUMMARY.json --output-dir .omega/fleet

# Corpus avec Fleet optionnel automatique
omega-summary-corpus \
  --workspace /path/to/repos \
  --depth 9 \
  --audience oak \
  --output-dir .omega/corpus-summary

# Exiger le Fleet lorsque le secret doit être présent
omega-summary-corpus ... --require-fleet

# Générer les propositions d'alias
omega-summary alias-proposals \
  IDENTITY_CONTINUITY.json \
  --output .omega/identity/ALIAS_PROPOSALS.json

# Approuver explicitement un alias
omega-summary alias-approve omega_old_t omega_new_t \
  --registry .omega/aliases/ALIAS_REGISTRY.json \
  --evidence-ref 'IDENTITY_CONTINUITY.json#candidate-1' \
  --approved-by reviewer

# Requête composée
omega-summary query-plan \
  CORPUS_SUMMARY.json query-plan.json \
  --output-dir .omega/query-plan
```

## Reusable workflow

Le workflow réutilisable conserve :

```yaml
permissions:
  contents: read
```

Le secret `fleet_salt` est optionnel.

- absent : aucun Fleet n'est émis;
- présent : le résumé D9 est projeté vers `fleet/`;
- le secret n'est pas écrit dans l'artefact;
- le workflow n'acquiert aucune permission d'écriture supplémentaire.

## Contrats R0.5

- `omega_summary_fleet.schema.json`;
- `omega_summary_fleet_history.schema.json`;
- `omega_summary_alias_registry.schema.json`;
- `omega_summary_query_plan.schema.json`.

Ils s'ajoutent aux contrats R0.1-R0.4.

## OAK boundaries

R0.5 impose :

```text
repository_token != repository authority
fleet dashboard != organization truth
alias candidate != approved alias
approved alias != scientific identity
aggregate != causal explanation
structural crystallization != scientific validation
```

Invariant directeur :

```text
OBSERVE MORE != CLAIM MORE
```

Invariant de confidentialité :

```text
AGGREGATE MORE != EXPOSE MORE
```

## Prochaines couches

1. registre explicite de preuves scientifiques/benchmarks externes;
2. mapping privé optionnel token -> dépôt, stocké hors artefact public;
3. fédération de plusieurs Fleet sans partager leurs sels;
4. requêtes sur séries temporelles de Fleet;
5. génération de plans d'action OAK à partir de dette structurelle, toujours review-only;
6. connecteurs INFO² / GitHub Brain / OAKGate / Rosette / Asset Factory.
