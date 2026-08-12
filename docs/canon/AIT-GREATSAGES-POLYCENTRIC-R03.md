# Ω-GREATSAGES-POLYCENTRIC-T∞ — R0.3 Contract

## Status

**Executable contract / software fixture. Not yet a global historical corpus.**

R0.3 prepares the GreatSages architecture for the Tristan dezoom from named individuals to a polycentric history of human knowledge.

## Mother invariant

```text
knowledge exists somewhere != actor has access to that knowledge
```

Therefore `t_world` and `t_accessible(actor, knowledge)` are different objects. Missing access evidence is `UNKNOWN_ACCESS`; it is never silently inferred from world existence.

## First-class knowledge carriers

- person
- collective
- school
- institution
- tradition
- civilization
- network
- anonymous community

No actor kind receives a built-in intelligence, importance, civilization or cultural ranking.

## Access graph

An `AccessibilityEdge` records:

```text
actor -> knowledge atom
+ accessible_from_year
+ language
+ optional translation bridge
+ directness
+ certainty
+ sources
```

Admission is fail-closed:

1. if the knowledge does not yet exist in the modeled world -> `BLOCKED_FUTURE`;
2. if no explicit actor-access edge exists by the date -> `UNKNOWN_ACCESS`;
3. if language is incompatible and no valid translation is available -> language/translation block;
4. otherwise -> `ALLOWED` with an evidence score.

## Translation loss

A translation bridge carries a `TranslationLossTensor`:

```text
lexical loss
semantic ambiguity
notation shift
context loss
```

The current aggregate is a transparent heuristic score, not an empirical universal law.

## Attribution Parallax

Attribution is represented as independent facets rather than a single `author` field:

- first known evidence
- independent discovery
- publication
- formalization
- popularization
- preservation
- translation
- instrumental enablement

This allows one knowledge object to have multiple legitimate historical roles without collapsing them into a single winner.

## Civilization Zoom Tensor

R0.3 can slice the atlas by:

```text
time
actors
regions
domains
languages
attribution roles
```

The operation is filtering/zooming, not ranking.

## Software fixture boundary

The initial R0.3 tests use intentionally synthetic actors and knowledge atoms. They validate the semantics of polycentric access without introducing unsupported historical claims.

Before real civilization-scale ingestion, each access edge, translation bridge and attribution facet should carry source-level provenance and uncertainty.

## OAK rules

1. world existence never implies actor accessibility;
2. missing access evidence stays unknown;
3. translation is not identity;
4. translation loss is explicit and uncertain;
5. first evidence != invention != publication != formalization != popularization;
6. collective knowledge is first-class;
7. anonymous contribution is allowed as a first-class actor type;
8. no culture/person ranking is required for the atlas;
9. no single-line history is assumed;
10. software validation does not certify historical truth.

## Next dezoom

```text
R0.3 contract
 -> sourced multilingual actor/access graph
 -> knowledge diffusion and independent-convergence graph
 -> translation genealogy
 -> collective-sage profiles
 -> recursive HGFM/Venn-Tristan civilization zoom
 -> Ω-HUMAN-KNOWLEDGE-GENOME-T∞
 -> Ω-CIVILIZATION-MIND-HGFM-T∞
```

## M−

- **M− access-by-existence:** an idea existing somewhere is treated as globally available. Correction: require actor-specific access evidence.
- **M− winner attribution:** one name absorbs discovery, formalization, translation and popularization. Correction: attribution parallax.
- **M− translation identity:** translated concepts are assumed semantically identical. Correction: explicit translation-loss tensor.
- **M− celebrity history:** anonymous/collective/institutional knowledge disappears. Correction: first-class collective and anonymous actors.
- **M− linear civilization story:** knowledge is forced into one civilization chain. Correction: polycentric access graph + zoom tensor.
