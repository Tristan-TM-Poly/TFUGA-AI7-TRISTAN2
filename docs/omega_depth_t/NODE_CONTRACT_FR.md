# Contrat documentaire d’un nœud Ω-DEPTH-T∞

Chaque objet récursif est un `NodeContract`.

## Identité

| Champ | Sens |
|---|---|
| `id` | Identifiant stable et hiérarchique |
| `name` | Nom humain |
| `depth` | Profondeur observée `n` |
| `path` | Chemin documentaire ou logiciel |
| `parent_id` | Nœud de profondeur `n-1` |
| `root_creation` | Création racine |

## Fonction

| Champ | Sens |
|---|---|
| `role` | Responsabilité du nœud |
| `inputs` | Entrées attendues |
| `outputs` | Sorties produites |
| `interfaces` | Contrats de communication |
| `dependencies` | Dépendances internes ou externes |
| `constraints` | Limites physiques, logicielles, légales ou produit |

## Discipline scientifique

| Champ | Sens |
|---|---|
| `scientific_basis` | Socle établi |
| `assumptions` | Hypothèses explicites |
| `invariants` | Propriétés à conserver |
| `failure_modes` | Conditions d’échec |
| `baselines` | Méthodes de comparaison |
| `tests` | Tests annoncés |
| `evidence` | Preuves liées |

## Gouvernance

| Champ | Sens |
|---|---|
| `oak_status` | Fertile, défini, codé, testé, benchmarké, mesuré ou validé |
| `code_status` | Absent, squelette, exécutable ou testé |
| `ip_status` | Public, révision requise, brevet potentiel ou secret |
| `risk_level` | Faible, moyen, élevé ou restreint |
| `m_plus` | Succès réutilisables |
| `m_minus` | Échecs, limites et résidus |

`metadata.atomic=true` n’interdit pas une future redécomposition. Il indique seulement qu’à l’état actuel le nœud est suffisamment précis pour être implémenté et testé.
