# Ω-SYNERGY-N-T — moteur de recherche d’ordre n de la Synergy Foundry

**Statut :** sous-moteur exécutable de Ω-SYNERGY-T∞ R1.  
**Autorité :** `review_only_heuristic`; aucune preuve, certification, publication, fusion, dépôt IP ou action externe automatique.

## Position canonique

Ω-SYNERGY-N-T n’est plus une architecture isolée. Il constitue le moteur combinatoire borné de :

```text
Ω-SYNERGY-T∞ / Tristan Synergy Foundry
  -> CreationDNA
  -> CreationGraph
  -> capability–need closure
  -> SynergyTensor
  -> Ω-SYNERGY-N-T beam search
  -> causal experiments
  -> ProofLedger
  -> PR Genome / PR Orchestra
  -> Meta-Synergy Reactor
  -> product hypotheses
```

La spécification canonique complète est `docs/canon/OMEGA_SYNERGY_T_INFINITY_R1.md`.

## Fonction

Pour `m` systèmes, l’énumération exhaustive des combinaisons d’ordre `n` exige `C(m,n)` évaluations. Le moteur utilise donc une recherche bornée :

1. compilation des dépôts en `CreationDNA`;
2. présélection par domaines, tokens, co-mentions et interfaces;
3. calcul d’un tenseur multiobjectif explicite;
4. conservation d’un faisceau fini;
5. extension vers les ordres `3..n`;
6. pénalisation de la dette, du risque, de l’incertitude et de l’ordre;
7. compilation des meilleurs candidats en expériences falsifiables.

La recherche peut manquer des combinaisons utiles. Ce résidu est une limite déclarée et doit alimenter M⁻ ou une stratégie de recherche alternative.

## Tenseur R1

Le classement expose séparément :

- résonance sémantique;
- complémentarité capacité–besoin;
- compatibilité d’interface;
- gain de fermeture;
- preuve disponible;
- préparation causale;
- réutilisation;
- valeur optionnelle;
- hypothèse produit;
- risque;
- coût d’intégration;
- incertitude;
- dette.

Le total scalaire sert uniquement à allouer un budget expérimental. Une proximité lexicale sans fermeture est marquée comme anti-synergie potentielle.

## Sorties

```text
reports/github-autonomous-reactor/synergy-foundry/
  creation_dna.json
  creation_graph.json
  creation_graph.dot
  synergy_report.json
  synergy_n.json
  closure_bridges.json
  portfolio.json
  experiment_queue.json
  counterfactual_twins.json
  pr_orchestra.json
  meta_synergies.json
  product_hypotheses.json
  SYNERGY_FOUNDRY_REPORT.md
```

Les anciens noms `system_inventory.json`, `research_queue.json`, `SYNERGY_N_REPORT.md` et `synergy_n.json` restent générés pour compatibilité.

## Commandes

```bash
omega-synergy \
  --repo-root . \
  --max-order 4 \
  --beam-width 96 \
  --top-k 25 \
  --portfolio-budget 4.0
```

La façade historique reste disponible :

```bash
python tools/github_reactor/synergy_n_engine.py \
  --repo-root . \
  --out reports/github-autonomous-reactor/synergy-foundry
```

## OAK et M⁻

- Co-mention n’est pas causalité.
- Similarité n’est pas complémentarité.
- Une interface doit déclarer ses pertes.
- Toute composition complexe doit battre une baseline plus simple.
- Toute expérience doit inclure ablation, contrôle, incertitude et rollback.
- Un hash-chain garantit l’intégrité du registre, pas la vérité du claim.
- La confiance possède une demi-vie et exige revalidation.
- Le workflow GitHub conserve `contents: read` et produit seulement des artefacts d’audit.
- Le PR Orchestra ne confère aucune autorité de fusion.
