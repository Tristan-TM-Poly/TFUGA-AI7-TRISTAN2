# Ω-SYNERGY-N-T — Recherche, analyse et synergies d’ordre n

**Statut :** D-MVP borné, déterministe, review-only.  
**Autorité :** aucune preuve scientifique, certification, publication, dépôt IP, fusion ou action externe automatique.

## Phrase-mère

Chaque système de Tristan devient un nœud documenté; chaque relation devient une arête mesurée; chaque combinaison d’ordre `n` devient une hypothèse de recherche priorisée, munie de baselines, ablations, résidus, incertitudes et mémoire M⁻.

```text
Dépôts + documents + code + tests + schémas
  -> découverte des systèmes
  -> normalisation canonique
  -> graphe de cooccurrence / domaines / preuves / risques
  -> synergies d’ordre 2
  -> beam search borné vers les ordres 3..n
  -> paquets de recherche falsifiables
  -> OAKGate
  -> prototype / expérience / publication / IP seulement après approbation
```

## Pourquoi une recherche bornée

Pour `m` systèmes, l’énumération complète exige `C(m,n)` combinaisons. Avec plusieurs centaines de systèmes, l’espace devient rapidement impraticable. Ω-SYNERGY-N-T utilise donc une recherche en faisceau :

1. présélection de paires par domaines, tokens, chemins partagés et co-mentions;
2. score pairwise déterministe;
3. conservation des meilleures frontières;
4. extension contrôlée vers l’ordre suivant;
5. pénalité croissante de complexité;
6. sortie des meilleurs candidats et des résidus M⁻.

Cette méthode peut manquer des combinaisons utiles. Ce manque est enregistré comme limite, pas caché.

## Score de synergie

Pour une combinaison `C={S1,...,Sn}` :

```text
Score(C) =
  0.48 * cohésion_pairwise
+ 0.16 * paire_bottleneck
+ 0.18 * couverture_domaines
+ 0.22 * niveau_preuve
- 0.18 * risque
- pénalité_ordre
```

Les facteurs pairwise utilisent :

- chevauchement lexical;
- chevauchement de domaines;
- complémentarité inter-domaines;
- co-mention dans les mêmes artefacts;
- niveau de preuve approximatif;
- pénalité de risque et de redondance.

Le score sert à **ordonner le travail**. Il ne mesure ni vérité, ni nouveauté brevetable, ni rendement industriel.

## Sorties automatiques

```text
reports/github-autonomous-reactor/synergy-n/
  system_inventory.json
  synergy_n.json
  research_queue.json
  SYNERGY_N_REPORT.md
  synergy_graph.dot
```

Chaque paquet de recherche contient les systèmes et l’ordre, une question de recherche, des requêtes proposées, des expériences, des ablations, les baselines requises et les portes OAK.

## Commandes

Analyse d’un dépôt :

```bash
python tools/github_reactor/synergy_n_engine.py \
  --repo-root . \
  --max-order 4 \
  --beam-width 96 \
  --top-k 25
```

Analyse multi-dépôts après plusieurs checkouts :

```bash
python tools/github_reactor/synergy_n_engine.py \
  --repo-root workspace/root \
  --repo-root workspace/deep-corpus \
  --repo-root workspace/ait-generator \
  --repo-root workspace/variant \
  --max-order 5 \
  --beam-width 128 \
  --top-k 30
```

## Boucle automatisée

```text
SCAN -> INVENTORY -> GRAPH -> SYNERGY(k) -> RESEARCH PACKETS
     -> OAK REVIEW -> TEST/ABLATION -> EVIDENCE UPDATE -> RESCORE
```

La prochaine version doit réinjecter les résultats expérimentaux dans le score afin qu’une synergie puisse monter, descendre ou être archivée selon les preuves réelles.

## OAK et M⁻

- Une co-mention documentaire n’implique pas une causalité.
- Une proximité lexicale n’implique pas une compatibilité mathématique ou physique.
- Une synergie bien notée reste une hypothèse.
- Une synergie scientifique exige unités, hypothèses, domaine de validité, baseline et incertitudes.
- Une synergie produit exige utilisateur, douleur, valeur, coût, concurrence et preuve d’usage.
- Une synergie IP exige provenance, antériorité et verrou de confidentialité.
- Le workflow reste en lecture seule et dépose seulement des artefacts d’audit.
