# HGFM Symbiotic Migration v0.1

Pipeline local-first pour migrer des archives Raman, scripts Python legacy et brouillons documentaires vers une forme HGFM / DCT++ vérifiable.

## Ce module contient

- `hgfm_symbiotic_migration.py` : migrateur autonome avec trois sous-systèmes : spectres Raman, inventaire de code Python, fusion documentaire.
- Un mode `--self-test` pour valider les fonctions critiques.
- Un mode `--demo` pour générer des exemples synthétiques et produire des rapports.
- Un workflow GitHub Actions racine : `.github/workflows/hgfm-symbiotic-migration.yml`.

## Commandes locales

```bash
python -m pip install numpy pandas
python tools/hgfm_symbiotic_migration_v0_1/hgfm_symbiotic_migration.py --self-test
python tools/hgfm_symbiotic_migration_v0_1/hgfm_symbiotic_migration.py --demo --out reports/hgfm_symbiotic_demo
```

## Politique de sécurité

Ce migrateur est volontairement non destructif : il lit les fichiers, génère des sorties et exige une revue humaine avant tout push, merge ou déploiement. Les données brutes Raman ne doivent pas être envoyées à Vercel. Vercel sert seulement au dashboard, à la documentation ou à une API légère.

## Statut canonique

- Statut : S2, prototype exécutable.
- Niveau de vérité : T1/T2 selon les données entrées.
- Canonisation : non canonique tant que les vrais jeux de données, checksums, tests de réplication et rapports DCT++ ne sont pas validés.
