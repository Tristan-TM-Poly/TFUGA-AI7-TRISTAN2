# Ω-GENERATOR-DISCOVERY-SCALE R0.4

## Campagnes multi-époques asymptotiquement sans plafond

**Statut :** infrastructure logicielle exécutable et OAK-safe. Les objets générés sont des candidats structurés et des benchmarks synthétiques. Ils ne deviennent pas des découvertes, preuves, validations expérimentales, brevets ou produits uniquement parce qu’ils existent en grand nombre.

## Décision d’architecture

R0.3 a démontré une campagne déterministe de :

- 131 072 candidats générateurs;
- 1 048 576 benchmarks synthétiques;
- 1 179 648 ajouts logiques.

R0.4 retire l’idée que cette cardinalité constitue une limite. Une exécution est découpée en **époques déterministes**, chacune ayant une empreinte différente, des identifiants globalement uniques, des partitions contiguës, des shards atomiques et des checkpoints.

```text
intention de volume
    ↓
budget fini de l’exécution
    ↓
plan multi-époques
    ↓
partitions indépendantes
    ↓
shards JSONL atomiques
    ↓
validation structurelle totale
    ↓
validation profonde des risques + échantillon déterministe
    ↓
M⁺ percée ou M⁻ saturation
    ↓
redesign → replay → expansion
```

Le budget d’une exécution n’est jamais canonisé comme plafond global.

## Profils fournis

Les profils sont des raccourcis de planification, pas des maxima :

| Profil | Ajouts logiques planifiés |
|---|---:|
| `million` | 1 179 648 |
| `ten-million` | 11 796 480 |
| `hundred-million` | 117 964 800 |
| `billion` | 1 179 648 000 |

Une valeur arbitraire peut être demandée avec `--target-records`. Le planificateur arrondit seulement à la frontière atomique d’un bundle générateur + benchmarks.

## Propriété de non-collision

Chaque époque reçoit :

- un `campaign_id` dérivé;
- une empreinte SHA-256 dérivée;
- un préfixe d’identifiant contenant l’époque et l’empreinte;
- des liens générateur→benchmarks réécrits avec le même namespace;
- une provenance incluant la campagne de base et l’époque.

Ainsi, deux époques peuvent être fusionnées sans collision, même lorsqu’elles utilisent le même index mixed-radix.

## Planification

```bash
omega-generator-scale plan \
  --profile billion \
  --summary-only
```

Plan personnalisé :

```bash
omega-generator-scale plan \
  --target-records 25000000000 \
  --target-records-per-partition 500000 \
  --bundles-per-shard 4096 \
  --output generated/scale/plan.json \
  --matrix-output generated/scale/matrix.json
```

Le plan contient seulement les métadonnées d’époques et de partitions. Il ne matérialise pas les milliards de payloads en mémoire.

## Émission atomique

```bash
omega-generator-scale emit \
  --profile hundred-million \
  --global-partition-index 0 \
  --bundles-per-shard 2048 \
  --output-dir generated/scale/p000
```

Reprise :

```bash
omega-generator-scale emit \
  --profile hundred-million \
  --global-partition-index 0 \
  --bundles-per-shard 2048 \
  --output-dir generated/scale/p000 \
  --resume
```

Chaque shard est écrit dans un fichier temporaire, synchronisé, puis déplacé atomiquement. Un ledger `shards.jsonl`, un `checkpoint.json` et un `report.json` permettent audit, reprise et rollback.

## Validation hiérarchique

R0.4 sépare deux couches :

1. **Structure totale** pour chaque bundle parcouru : cardinalité, ordre, unicité locale, liens générateur↔benchmarks, empreinte du flux.
2. **Validation profonde** pour tous les risques configurés et un échantillon déterministe : provenance, OAK gate, nombres finis, générateur parent exact et invariant de sortie finie.

```bash
omega-generator-scale validate \
  --epoch-index 0 \
  --start 0 \
  --generator-bundles 16384 \
  --sample-ppm 10000
```

`sample-ppm=10000` correspond à 1 % des bundles non déjà couverts par la validation exhaustive des risques. Le taux est une politique modifiable, pas une constante de vérité.

## Mémoire positive et négative

Une observation de frontière contient :

- volume demandé et traité;
- succès ou échec;
- qualité;
- pression par dimension;
- durée;
- octets écrits;
- notes reproductibles.

Le contrôleur produit :

- `M+_breakthrough` lorsque la campagne est saine et recommande une expansion multiplicative;
- `M-_saturation` lorsque qualité, pression ou exécution imposent réduction temporaire, redesign et replay.

```bash
omega-generator-scale frontier observation.json \
  --ledger generated/scale/frontier.jsonl
```

La recommandation suivante est un budget fini expérimental. Elle n’est jamais un plafond permanent.

## Compatibilité GitHub

`--matrix-output` génère une matrice légère contenant uniquement :

- index global de partition;
- index d’époque;
- début et fin de bundles;
- nombre d’ajouts logiques.

Les payloads ne sont pas injectés dans la définition GitHub Actions. Les très grandes campagnes doivent être exécutées en vagues respectant les quotas, le stockage, la durée CI, les coûts et les autorisations.

## Invariants OAK

```text
volume généré ≠ densité de preuve
benchmark synthétique ≠ expérience réelle
empreinte stable ≠ vérité scientifique
absence d’erreur de schéma ≠ validité du modèle
partition réussie ≠ campagne universellement scalable
plan milliard ≠ émission milliard accomplie
émission accomplie ≠ utilité
utilité ≠ brevetabilité
```

Toute promotion scientifique exige encore unités, données, baseline, incertitude, domaine de validité, contrôles négatifs, falsification, comparaison et reproduction appropriée.

## Règle canonique

> Les nombres 1M, 10M, 100M et 1B sont des profils de charge. Aucun n’est un plafond. Toute saturation observée est enregistrée dans M⁻, attaquée architecturalement, rejouée, puis promue en M⁺ seulement après réussite reproductible avec qualité et rollback préservés.
