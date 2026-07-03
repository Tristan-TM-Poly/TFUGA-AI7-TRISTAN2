# Ω-Absorber v2 — ZERO-TOUCH Roadmap

## But

Faire évoluer `Ω-PDF-HYPERGRAPH-GITHUB-T / AIT-Frédéric` de simple absorption vers un système complet : absorber, chercher, canoniser, mémoriser les échecs, préparer les actions GitHub, sans publier de contenu sensible.

## Nouveaux modules v2

### `omega_prof_poly_t.absorb_query`

Lit les sorties de `omega-corpus-absorb` et fournit :

- recherche locale dans `chunks.jsonl` et `claims.jsonl`;
- classement par pertinence simple;
- rendu Markdown OAK-safe;
- génération de `canon_packets.jsonl` candidats;
- tests/proof-obligations automatiques pour chaque claim.

Commandes :

```bash
omega-absorb-query search generated/omega_corpus "CVCD HGFM OAK" --limit 10
omega-absorb-query canon generated/omega_corpus --max-packets 20 --write
```

### `omega_prof_poly_t.drive_manifest_adapter`

Convertit un inventaire Drive exporté en manifest normalisé sans télécharger de contenu privé.

Commandes :

```bash
omega-drive-manifest drive_files.json --audit --output generated/drive_manifest.normalized.json
```

Statut OAK : metadata-only. Le téléchargement réel nécessite OAuth least privilege et une étape séparée.

### `omega_prof_poly_t.mminus_absorber`

Mémoire négative append-only pour les erreurs d'extraction, PDF sans texte, risques IP, claims bloqués et signaux de surconfiance.

Commandes :

```bash
omega-mminus-absorb ingest-oak generated/omega_corpus/oak_report.json --registry generated/m_minus_absorber.jsonl
omega-mminus-absorb summary --registry generated/m_minus_absorber.jsonl
```

## Flux complet v2

```text
1. Export Drive metadata -> omega-drive-manifest
2. ZIP/PDF/local corpus -> omega-corpus-absorb
3. OAK report -> omega-mminus-absorb
4. Search/query -> omega-absorb-query search
5. Claim candidates -> omega-absorb-query canon
6. Canon packets -> GitHub issues/branches/tests, après gates OAK
```

## Verrous OAK

- `publishable=false` par défaut.
- Aucun contenu Drive n'est téléchargé par le manifest adapter.
- Aucune invention/brevet n'est publiée sans triage IP.
- Les canon packets sont des candidats, pas des vérités.
- Les erreurs deviennent M⁻ au lieu d'être effacées.

## Prochain saut v3

- `github_issue_emitter` dry-run puis approbation explicite.
- extraction PDF page/bbox plus riche;
- OCR séparé avec confidence tensor;
- `claim_evidence_residue_graph` complet;
- index SQLite/FTS local;
- interface de requête GraphML/JSON;
- pont privé Drive↔GitHub avec moindre privilège.
