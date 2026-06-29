# Free Cloud Auto Meta-Generation

**Statut OAK :** automation gratuite, bornée, sans API externe et sans secret utilisateur.  
**Compute utilisé :** GitHub Actions sur dépôt public, avec `GITHUB_TOKEN` automatique.  
**Objectif :** exécuter périodiquement les itérations FTPCI-Ω sans serveur personnel, sans clé API et sans intervention manuelle.

---

## 1. Principe

Le dépôt contient maintenant un moteur stdlib-only :

```text
sage_tristan/auto_meta_generator.py
scripts/run_auto_meta_generation.py
```

et un workflow GitHub Actions :

```text
.github/workflows/auto-meta-generation.yml
```

Après merge sur `main`, GitHub Actions pourra lancer automatiquement :

```text
FTPCI-Omega Auto Meta-Generation
```

---

## 2. Cadence gratuite et bornée

Cadence planifiée :

```cron
17 5 * * *
```

Donc une fois par jour, à 05:17 UTC.

Raison OAK : cadence assez fréquente pour accumuler des itérations, assez faible pour éviter gaspillage, abus de compute gratuit, bruit et dette de rapports.

---

## 3. Ce que le workflow fait automatiquement

1. checkout du repo ;
2. setup Python 3.11 ;
3. compilation de sécurité avec `py_compile` ;
4. run FTPCI-Ω auto meta-generation ;
5. génération de rapports ;
6. commit automatique des rapports si quelque chose change.

Sorties :

```text
reports/auto_meta_generation_latest.json
reports/auto_meta_generation_latest.md
examples/auto_meta_generation_latest.summary.json
```

---

## 4. Sans clé API externe

Le système n'utilise pas :

- OpenAI API ;
- cloud payant ;
- secrets ;
- clés personnelles ;
- base de données externe ;
- serveur à maintenir.

Il utilise uniquement :

```text
GitHub Actions + Python standard library + GITHUB_TOKEN automatique
```

---

## 5. Limites honnêtes

- Les workflows planifiés GitHub Actions ne s'exécutent qu'après merge du workflow sur la branche par défaut.
- GitHub peut désactiver les workflows inactifs ou limiter l'usage selon les règles du compte/repo.
- Le moteur actuel génère des priorités méta-théoriques; il ne prouve pas de claims physiques.
- Les sorties doivent passer par OAK avant canonisation.

---

## 6. Architecture de sécurité OAK

Le workflow est volontairement limité :

```text
no secrets
no external network calls by code
no paid cloud
daily cadence
10 minute timeout
reports only
```

Il ne peut pas déployer, acheter, appeler des APIs payantes, ni agir hors du dépôt.

---

## 7. Extension future gratuite

Extensions possibles sans demander de clés :

1. ajouter tests unitaires ;
2. générer un codex 1 page du top candidat ;
3. générer 16 hypothèses testables ;
4. produire un fichier `memory_negative.jsonl` ;
5. utiliser GitHub Pages pour publier les rapports ;
6. utiliser les artefacts GitHub Actions pour conserver les logs.

---

## 8. Formule canonique

```math
FreeCloud_{Tristan}
=
GitHubActions
\circ
PythonStdlib
\circ
FTPCI\Omega
\circ
OAK
\circ
Reports
```

Résumé : le repo devient un petit serveur gratuit d'itérations méta-génératives, avec limites OAK strictes et sans dépendance externe.
