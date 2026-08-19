# Ω-DEPTH-T∞ — Architecture récursive des créations de Tristan

Ω-DEPTH-T∞ transforme chaque création en une arborescence probatoire où tout nœud de profondeur `n` est un sous-système explicite d’un nœud de profondeur `n-1`.

```text
création → systèmes → sous-systèmes → modules → composants
→ opérateurs → fonctions → tests → cas → preuves → résidus → M⁺/M⁻
```

## Règle canonique

\[
C^{(n)} = \operatorname{Decompose}(C^{(n-1)})
\]

La profondeur observée d’un artefact fini n’est **jamais** un plafond permanent. Une branche cesse localement d’être décomposée lorsqu’elle devient suffisamment atomique pour posséder des interfaces explicites, un test définissable, une preuve attendue et des conditions d’échec.

## Paquet exécutable

Le paquet `omega_depth_t` fournit :

- `NodeContract` : contrat machine de chaque nœud;
- `DepthGraph` : graphe parent-enfant validé;
- registre des 40 créations majeures;
- générateur OAKGate jusqu’à la profondeur observée `n=9`;
- export JSON, JSONL, Markdown et GraphML;
- scaffold d’une racine pour chaque création;
- commandes de navigation et de validation.

## Démarrage

```bash
python -m pytest tests/test_omega_depth_t.py
omega-depth roots
omega-depth scaffold-all --output-dir generated/omega_depth_t/roots
omega-depth oakgate-example --output-dir generated/omega_depth_t/oakgate-depth9
omega-depth validate generated/omega_depth_t/oakgate-depth9/depth-graph.json
```

Le schéma se trouve dans [`schemas/omega-depth-node.schema.json`](../../schemas/omega-depth-node.schema.json).

## Garde-fou OAK

Chaque profondeur supplémentaire doit augmenter au moins une dimension : précision, testabilité, modularité, réutilisabilité, performance, sécurité, valeur scientifique, valeur produit ou valeur IP. Les budgets employés pendant une exécution sont révisables et ne constituent jamais des plafonds ontologiques.
