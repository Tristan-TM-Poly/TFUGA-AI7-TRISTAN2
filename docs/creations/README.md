# Atlas des créations de Tristan

> Une infrastructure scientifique, technologique et entrepreneuriale en construction.

Les créations de Tristan forment un écosystème commun. Certaines sont des architectures générales; d’autres sont des théories exploratoires, des logiciels, des méthodes d’analyse, des moteurs de validation ou des directions de produits.

Chaque fiche distingue explicitement la **vision**, les **applications**, le **produit potentiel**, le **statut OAK** et la **prochaine preuve attendue**.

## Décomposition récursive à profondeur n

Chaque fiche de cet atlas est désormais une racine `n=0` du moteur **Ω-DEPTH-T∞**.

```text
création n=0
→ systèmes n=1
→ sous-systèmes n=2
→ modules n=3
→ composants n=4
→ opérateurs n=5
→ fonctions n=6
→ tests n=7
→ cas n=8
→ preuves et résidus n≥9
```

- [Documentation Ω-DEPTH-T∞](../omega_depth_t/README_FR.md)
- [Contrat d’un nœud récursif](../omega_depth_t/NODE_CONTRACT_FR.md)
- [Exemple OAKGate jusqu’à n=9](../omega_depth_t/OAKGATE_DEPTH_9_FR.md)
- [Registre généré des 40 racines](../../generated/omega_depth_t/roots/README.md)

La profondeur observée d’une exécution est un résultat fini, jamais un plafond permanent. Une branche s’arrête localement lorsqu’elle devient suffisamment atomique, interfacée, testable et probatoire.

## Orchestration de tous les dépôts et PR

**Ω-GITHUB-MYCELIUM-T∞** relie les racines récursives de l’atlas aux dépôts, pull requests, artefacts, tests, preuves, risques, produits et mémoires globales de Tristan.

```text
intention
→ création racine
→ profondeur n
→ contrats et artefacts
→ routage public/privé
→ campagnes multi-dépôts
→ plans de PR dépendants
→ CI-OAK
→ EvidenceBundle
→ M⁺ / M⁻
→ proposition de synchronisation du canon
```

- [Architecture et utilisation Ω-GITHUB-MYCELIUM-T∞](../omega_github_mycelium_t/README_FR.md)
- [Spécification des campagnes multi-dépôts](../omega_github_mycelium_t/MULTIREPO_CAMPAIGN_SPEC.md)
- [Frontières d’automatisation et de souveraineté](../omega_github_mycelium_t/AUTOMATION_BOUNDARIES.md)
- [Snapshot initial des dépôts autorisés](../../data/omega_github_mycelium_t/repository_snapshot_2026_08_03.json)

Commande principale :

```bash
omega-mycelium plan \
  --objective "Développer une création et ses preuves" \
  --root-creation omega-doc-t \
  --snapshot generated/omega_github_mycelium_t/live-snapshot.json \
  --output-dir generated/omega_github_mycelium_t/campaign
```

R0.1 automatise la lecture, la compilation, le routage, la planification, l’audit et les rapports. Les branches, commits, PR, fusions, publications, déploiements, suppressions et changements de permissions restent des actions séparément autorisées et humainement contrôlées.

## I. Noyau de l’architecture Tristan

1. [HGFM — Hypergraphes Fractals Mycéliens](./01_hgfm.md)
2. [LOG — Compression structurée](./02_log.md)
3. [CVCD — Compression et invariants fertiles](./03_cvcd.md)
4. [EXP — Décompression générative](./04_exp.md)
5. [OAK — Validation et falsification](./05_oak.md)
6. [M⁺ / M⁻ — Mémoire des succès et des échecs](./06_m_plus_m_minus.md)
7. [Ω-UNC²-T — Incertitude de l’incertitude](./07_omega_unc2_t.md)
8. [Ω-SANS-PLAFOND-T∞](./08_omega_sans_plafond_t.md)

## II. Intelligence artificielle, documentation et connaissance

9. [SAGE-Tristan](./09_sage_tristan.md)
10. [AI-7 / AIT-PANTHEON](./10_ai7_ait_pantheon.md)
11. [Ω-DOC-T — Documentation de Tristan](./11_omega_doc_t.md)
12. [Ω-ROSETTE-T — Absorption scientifique multimodale](./12_omega_rosette_t.md)
13. [Ω-PDF-HYPERGRAPH-GITHUB-T](./13_omega_pdf_hypergraph_github_t.md)
14. [Ω-WEB-HG-T∞ — Hypergraphe Web probatoire](./14_omega_web_hg_t.md)
15. [WikiForge-T / Ω-WIKI-T∞](./15_wikiforge_t.md)
16. [Ω-OSS-DIGEST-T](./16_omega_oss_digest_t.md)
17. [Ω-GDM-T — Google Drive Manager](./17_omega_gdm_t.md)

## III. Mathématiques et transformations

18. [Ω-TRANSFORM-T](./18_omega_transform_t.md)
19. [FFWT — Fast Fractal Wavelet Transform](./19_ffwt.md)
20. [FFWT-HAC-CVCD](./20_ffwt_hac_cvcd.md)
21. [Ω-ZETA-MANDEL-T](./21_omega_zeta_mandel_t.md)
22. [Ω-LOGEXP-MORPH-T∞²](./22_omega_logexp_morph_t.md)

## IV. Matière, molécules et fabrication

23. [Ω-FCRYST-T — Cristaux fractals](./23_omega_fcryst_t.md)
24. [Ω-ORG-FAM-T — Familles de molécules organiques](./24_omega_org_fam_t.md)
25. [Ω-OEMMTD-T](./25_omega_oemmtd_t.md)
26. [Ω-3DP-T — Fabrication additive](./26_omega_3dp_t.md)
27. [Ω-PROTEIN-FOLD-T](./27_omega_protein_fold_t.md)

## V. Physique, énergie et systèmes

28. [Ω-CIRCUITS-T](./28_omega_circuits_t.md)
29. [Ω-ENERGY-T](./29_omega_energy_t.md)
30. [Ω-EMR-SOURCE-T∞](./30_omega_emr_source_t.md)
31. [Ω-SPACE-SYSTEMS-T∞](./31_omega_space_systems_t.md)
32. [Ω-NATSCI-T](./32_omega_natsci_t.md)

## VI. Logiciel, ingénierie et entrepreneuriat

33. [Ω-RE-T∞ — Reverse Engineering de Tristan](./33_omega_re_t.md)
34. [Ω-AUTO²-T — Automatisation de l’automatisation](./34_omega_auto2_t.md)
35. [OAKGate GitHub Factory](./35_oakgate_github_factory.md)
36. [Ω-REV-T — Revenus de Tristan](./36_omega_rev_t.md)
37. [Tristan Asset/IP/Revenue Classifier](./37_asset_ip_revenue_classifier.md)
38. [Ω-PROF-POLY-T](./38_omega_prof_poly_t.md)

## VII. Cognition, organisation et philosophie appliquée

39. [Ω-NEG-T — Néguentropie de Tristan](./39_omega_neg_t.md)
40. [Ω-JKD-T — Jeet Kun de Tristan](./40_omega_jkd_t.md)

## Discipline commune

Chaque création suit la formule :

> **Création Tristan = Vision + Formalisation + Code + Test + Preuve + Produit potentiel + Mémoire**

Une création sans code peut encore être une théorie. Une création sans preuve peut encore être une hypothèse. Une création sans utilisateur peut encore être un prototype. Son statut doit toujours être explicite.

Le pipeline commun est :

```text
idées → modèles → code → simulations → expériences → preuves → technologies → produits → entreprises → nouvelles capacités de création
```
