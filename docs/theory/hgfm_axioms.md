# Axiomes THT / HGFM

Statut : **OAK-3 / ACTIVE**.  
Ces axiomes sont des règles fondatrices pour développer la théorie des Hypergraphes de Tristan sans confondre vision, hypothèse, prototype, mesure et preuve.

---

## Axiome 1 — Trace

```math
\forall x,\ Exist(x) \Rightarrow \exists \tau_x
```

Tout ce qui compte dans le système doit laisser une trace exploitable.

---

## Axiome 2 — Transformation

```math
Operational(x) \Rightarrow \exists T : x \mapsto y
```

Un objet vivant, utile ou opératoire transforme ou est transformable.

---

## Axiome 3 — Maintien

```math
Structure(x) \Rightarrow Persist(x,\Delta t)
```

Une structure doit se maintenir dans le temps pour être autre chose qu’une apparition locale.

---

## Axiome 4 — Mémoire

```math
Trace(x)+Index(x)+Reuse(x) \Rightarrow Memory(x)
```

La mémoire est une trace indexée et réutilisable.

---

## Axiome 5 — Hyperrelation

```math
Relation(x,y) \subset HyperRelation(X,Y)
```

La relation binaire est un cas pauvre ; les systèmes réels sont hyperrelationnels.

---

## Axiome 6 — Multi-échelle

```math
Robust(x) \Rightarrow \exists P_\sigma(x)
```

Un objet robuste possède des projections multi-échelles.

---

## Axiome 7 — Projection incomplète

```math
x \neq P_{\lambda,\sigma}(x)
```

Une projection n’est jamais le réel total. Toute projection a un résidu.

---

## Axiome 8 — Résidu

```math
\forall T,x,\quad R(T,x) \neq \emptyset
```

Toute transformation laisse un résidu : erreur, incertitude, coût, contradiction potentielle ou information non compressée.

---

## Axiome 9 — OAK

```math
Canon(x) \Rightarrow Attack(x)
```

Rien n’entre au canon sans attaque, test, preuve ou falsification tentée.

---

## Axiome 10 — Mémoire négative

```math
Failure(x) \Rightarrow M^-(x)
```

Toute erreur importante doit devenir mémoire négative si elle peut empêcher une répétition future.

---

## Axiome 11 — Fertilité

```math
Fertile(x) \Rightarrow \exists y_1,\dots,y_n
```

Une structure fertile génère de nouvelles structures : hypothèses, tests, prototypes, preuves, revenus, collaborations.

---

## Axiome 12 — Non-confusion épistémique

```text
FERTILE != PROVEN
ACTIVE != CERTIFIED
PREDICTED != MEASURED
UNKNOWN != FALSE
SIMULATED != REAL
```

Les statuts doivent rester séparés.

---

## Axiome 13 — Compression

```math
Useful(x) \Rightarrow \exists LOG(x)
```

Ce qui est utile peut souvent être compressé en invariants sans perte totale de structure.

---

## Axiome 14 — Expansion

```math
Invariant(c) \Rightarrow EXP(c)
```

Un invariant fertile peut être redéployé en applications, preuves, prototypes, tâches ou agents.

---

## Axiome 15 — Incomplétude fertile

```math
Rich(System) \Rightarrow Possible(System) > Provable_{local}(System)
```

Un système riche contient plus de possibles que ce qu’il peut prouver localement.

---

## Axiome 16 — Calcul borné

```math
Compute(System) < Possibles(System)
```

Le calcul est borné ; il faut filtrer, compresser, prioriser.

---

## Axiome 17 — Canon évolutif

```math
Canon_t \neq Canon_{t+1}
```

Le canon est stable, mais révisable sous preuve, contre-exemple ou mesure meilleure.

---

## Axiome 18 — Zéro auto-certification

```math
Claim(x) \not\Rightarrow Truth(x)
```

Une affirmation ne se valide jamais elle-même.

---

## Axiome 19 — Agentivité bornée

```math
AIT_i \Rightarrow Trace(AIT_i)+OAK(AIT_i)+Memory(AIT_i)
```

Tout agent doit laisser des traces vérifiables, des résidus et un statut OAK.

---

## Axiome 20 — Expansion responsable

```math
EXP(x) \Rightarrow OAK(EXP(x)) + M^-(risks)
```

Toute expansion doit prévoir ses erreurs possibles.

---

# Règle dure du canon

```math
Canon(x) \Rightarrow Definition(x)+Evidence(x)+Attack(x)+Residue(x)+Reuse(x)
```

Sans preuve, test, mesure ou prototype reproductible, un objet reste fertile/actif, pas canon.
