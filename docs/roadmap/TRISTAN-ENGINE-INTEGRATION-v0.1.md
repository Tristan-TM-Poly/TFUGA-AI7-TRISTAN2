# Tristan Engine Integration Roadmap v0.1

**Statut OAK :** intégration prototype. Les moteurs sont déterministes, stdlib-only, et doivent être testés avant promotion.

---

## 1. Moteurs intégrés

| Moteur | Fichier | Fonction |
|---|---|---|
| FTPCI-Ω Auto Meta Generation | `sage_tristan/auto_meta_generator.py` | génère des méta-théories candidates, Top16/Bottom16 |
| AIT-PANTHEON-Ω | `sage_tristan/ait_pantheon.py` | génère 16 rôles × 16 modes AIT, OAK, codex |
| JKD-YY3-Tristan² | `sage_tristan/jkd_yy3_tristan2.py` | sélectionne le générateur minimal fertile sous JKD/OAK |

---

## 2. Commandes locales

```bash
python -m unittest tests/test_tristan_engines.py
python scripts/run_auto_meta_generation.py
python scripts/run_ait_pantheon_cycle.py
python scripts/run_jkd_yy3_tristan2.py
python scripts/run_all_tristan_engines.py
```

---

## 3. Pipeline recommandé

```text
1. Run tests
2. Run all engines
3. Inspect reports/tristan_combined_latest.md
4. Decompress top1 into codex/test/prototype
5. Add failures to memory negative
6. Repeat with new salt or real data
```

---

## 4. OAK promotion gates

Un moteur ou une sortie ne monte en statut que si :

```text
traceable = true
prototype_path = true
tests_pass = true
oak_score >= threshold
hype <= threshold
negative_memory_updated = true
```

---

## 5. Next best step

Ajouter une couche `canon_compiler.py` qui prend le Top1 de chaque moteur et crée automatiquement :

1. une fiche canonique ;
2. une attaque OAK ;
3. un test minimal ;
4. une entrée mémoire positive/négative ;
5. une issue ou PR GitHub si demandé explicitement.

---

## 6. Sceau

```math
FTPCI\Omega + AIT\Omega + JKD\text{-}YY3\text{-}Tristan^2
= \text{machine de génération vérifiable}
```
