# omega_gov_qc_t

Prototype minimal pour **Ω-GOV-QC-T / TristanGovGraph Québec**.

Ce module transforme des entités gouvernementales publiques en graphe vérifiable et applique un OAKGate gouvernemental avant tout usage analytique.

## Principes

- Données ouvertes ou explicitement autorisées par défaut.
- Pas de décision sensible autonome.
- Sorties classées : signal, hypothèse, preuve structurée, recommandation, décision humaine.
- Chaque noeud doit conserver provenance, statut OAK et limites.
- Toute anomalie contractuelle ou administrative reste un signal, jamais un verdict.

## Structure

```text
omega_gov_qc_t/
  src/omega_gov_qc_t/
    gov_graph.py
    oak_gate.py
  schemas/
    gov_node.schema.json
  examples/
    qc_government_seed.json
```

## Exemple conceptuel

```python
from omega_gov_qc_t import GovNode, GovGraph, OAKGate

node = GovNode(
    node_id="ministry:mcn",
    name="Ministère de la Cybersécurité et du Numérique",
    node_type="ministry",
    source="public_government_directory",
    oak_status="B",
)

graph = GovGraph()
graph.add_node(node)

report = OAKGate().evaluate_context(
    use_case="open_data_mapping",
    contains_personal_data=False,
    makes_sensitive_decision=False,
    source_is_authorized=True,
    human_review_required=False,
)

assert report.deployable is True
```

## Prochains pas

1. Ajouter ingesteur Données Québec.
2. Ajouter normalisation ministères/organismes/municipalités.
3. Ajouter export NetworkX/JSON.
4. Ajouter rapports Markdown.
5. Ajouter CLI `omega-gov-qc`.
6. Ajouter dashboard/API.
