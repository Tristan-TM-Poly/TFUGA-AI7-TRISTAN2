# Ω-VALUE-OS-T∞ R0.1 — Constitution exécutable des valeurs

**Statut :** noyau logiciel de gouvernance et de sélection, `review_only`.  
**Portée :** théories, expériences, logiciels, agents, produits et décisions.  
**Non-portée :** aucun score n'est une probabilité de vérité, une certification de sécurité, un avis juridique, une preuve scientifique, une validation commerciale ou une autorisation d'action externe.

## 1. Mission

Ω-VALUE-OS-T∞ transforme des valeurs déclarées en contrats auditables :

```text
valeur
→ définition
→ métriques
→ hard gates
→ preuves
→ incertitude
→ résidus / M−
→ décision bornée
→ prochaine expérience ou revue humaine
```

Le système vise simultanément :

```text
maximum d'ambition dans l'espace des possibilités
maximum de rigueur dans l'espace des affirmations
minimum de dispersion dans l'espace de l'exécution
```

## 2. Objet fondamental

Une création candidate est représentée par un `ValueCase` qui conserve :

- identité et contexte;
- cinq hard gates constitutionnels;
- dimensions de valeur bornées dans `[0,1]`;
- dettes de cristallisation, confiance, technique et risque;
- niveau et force d'évidence;
- force de revendication;
- fermeture de l'artefact et réutilisabilité;
- incertitude;
- réversibilité et niveau d'autonomie;
- valeur heuristique de l'action immédiate versus information supplémentaire;
- provenance, falsificateurs et hypothèses.

Les nombres sont des **entrées de gouvernance**. Ils doivent provenir de mesures, reçus ou jugements explicitement documentés lorsqu'ils sont utilisés hors fixtures.

## 3. Constitution

### Article I — Intégrité

La force d'une revendication ne peut dépasser son plafond d'évidence. R0.1 emploie un plafond conservateur :

```text
claim_ceiling = evidence_strength × (1 - 0.5 × uncertainty)
```

C'est une règle de gouvernance et non une loi probabiliste.

### Article II — Traçabilité

Les décisions importantes doivent conserver provenance critique, version et digests. Un booléen de gate ne remplace pas les références détaillées; l'absence de références déclenche un avertissement.

### Article III — Falsifiabilité

Une proposition scientifique devrait déclarer :

- hypothèses;
- test discriminant;
- résultat qui la réfuterait;
- baseline concurrente;
- portée de validité.

L'absence de falsificateur n'accorde jamais une promotion scientifique silencieuse.

### Article IV — Sécurité

Les gates `safety`, `legality` et `consent` sont non compensatoires. Une utilité ou valeur externe élevée ne peut jamais compenser leur échec.

### Article V — Souveraineté

```text
automation capability != automation authority
```

Les niveaux sont :

- A0 observer;
- A1 recommander;
- A2 produire un brouillon;
- A3 exécution réversible bornée;
- A4 conséquences bornées significatives;
- A5 conséquences élevées.

R0.1 n'exécute aucune action externe. A4/A5 sans approbation humaine explicite sont bloqués; A3 exige une réversibilité minimale.

### Article VI — Cristallisation

La fertilité seule ne suffit pas. Le moteur pénalise les dettes et mesure explicitement la fermeture de l'artefact.

### Article VII — Réalité

La montée en niveau d'évidence suit :

```text
E0 self-evaluation
→ E1 automated tests
→ E2 independent benchmark
→ E3 external user
→ E4 external replication
→ E5 repeated external value
```

Le niveau E5 ne donne toujours aucune autorité si un hard gate échoue.

## 4. Les sept kernels

### Truth Kernel

Truth + Evidence + Falsifiability + Uncertainty + Claim Ceiling.

### Memory Kernel

Provenance + Replay + M⁺ + M⁻ + Version/Time.

### Representation Kernel

RPU + HGFM + CVCD + MultiScale + Invariants. R0.1 ne réimplémente pas ces moteurs; il leur réserve une place constitutionnelle et une interface future.

### Creation Kernel

Generativity + Diversity + Synergy + Compounding.

### Crystallization Kernel

Closure + WIP + Simplicity + Maintainability.

### Action Kernel

Safety + Sovereignty + Least Privilege + Reversibility.

### Reality Kernel

Utility + External Proof + Distribution + Venture + External Value.

## 5. Valeurs opératoires couvertes

R0.1 cristallise les familles développées dans le corpus :

1. vérité probatoire;
2. falsifiabilité;
3. incertitude de l'incertitude;
4. mémoire M⁺/M⁻;
5. provenance;
6. reproductibilité;
7. invariants;
8. représentation avant calcul;
9. moindre calcul;
10. multi-échelle;
11. nécessité d'hypergraphe;
12. générativité;
13. pression de fermeture;
14. dette de cristallisation;
15. Definition of Done;
16. WIP/anti-dispersion;
17. funnel exploration→sélection;
18. réversibilité;
19. souveraineté;
20. moindre privilège;
21. safety-by-construction;
22. simplicité;
23. utilité;
24. testabilité;
25. protection/IP;
26. venture;
27. preuve externe;
28. distribution;
29. composabilité;
30. réutilisabilité;
31. interopérabilité;
32. compounding;
33. autonomie opérationnelle;
34. centralité de l'intention;
35. ambition haute / revendication bornée;
36. Pareto;
37. constitution;
38. tribunal OAK;
39. abstention;
40. closure;
41. reality distance;
42. coût d'opportunité;
43. time-to-proof;
44. maintenabilité;
45. graceful failure;
46. explicabilité;
47. diversité;
48. indépendance des preuves;
49. version/temps;
50. méta-gouvernance.

R0.1 n'affirme pas que les 50 concepts sont tous complètement implémentés. Il implémente le **socle commun** qui permet de les rendre calculables progressivement : gates, vecteur de valeurs, dettes, evidence ladder, claim ceiling, abstention, Pareto, autonomie, réversibilité, portfolio et reçus déterministes.

## 6. Hard gates non compensatoires

```text
G = integrity ∧ safety ∧ legality ∧ consent ∧ critical_provenance
```

R0.1 ajoute aussi deux blockers conditionnels :

- violation du claim ceiling;
- autorité A4/A5 sans approbation humaine ou A3 avec réversibilité insuffisante.

Si un blocker existe :

```text
status = BLOCKED
effective_value = 0
```

Le moteur continue à exposer les métriques diagnostiques afin de montrer pourquoi une idée séduisante reste bloquée.

## 7. Optimisation douce

Pour les dimensions compensatoires, R0.1 emploie une moyenne géométrique pondérée :

```text
Q = exp( Σ wᵢ ln(max(qᵢ, ε)) / Σ wᵢ )
```

La géométrie évite qu'une très bonne dimension masque complètement une dimension presque nulle.

Les profils changent les poids selon le contexte :

- `research` : vérité, évidence et testabilité dominent;
- `software` : cristallisation, testabilité et maintenabilité dominent;
- `venture` : utilité, preuve externe et valeur externe montent;
- `high_consequence` : vérité, évidence et souveraineté dominent avec plancher d'évidence plus élevé.

Les valeurs restent stables; leurs poids sont contextuels.

## 8. Dettes

La pénalité R0.1 est :

```text
debt_penalty = exp(-(Dcrystal + Dconfidence + Dtechnical + Drisk))
```

Les dettes ne sont pas effacées par un bon score de fertilité. Elles doivent être réduites ou justifiées.

## 9. Valeur effective

Pour un candidat admissible :

```text
Veffective = Q
           × debt_penalty
           × external_evidence_factor
           × closure_factor
           × reuse_factor
```

Pour un candidat bloqué, la valeur d'action est forcée à zéro.

`Veffective` est un **indice de routage interne**, pas une valeur monétaire et pas une probabilité.

## 10. Abstention comme résultat valide

Si :

```text
evidence_strength < profile.evidence_floor
AND expected_information_value > expected_action_value
```

alors :

```text
ABSTAIN_MORE_EVIDENCE
```

Ce statut signifie qu'acquérir une information discriminante est préférable à une action immédiate. Il ne signifie pas abandonner la branche.

## 11. Pareto plutôt que score unique

Un portfolio reçoit aussi un front de Pareto sur :

```text
truth, evidence, utility, testability, crystallization, simplicity
```

Une option dominée peut être écartée sans prétendre qu'un score unique encode toute la décision. L'appartenance au front n'est jamais une approbation.

## 12. Coût d'opportunité

R0.1 calcule le gap de valeur effective vers la meilleure alternative disponible. C'est une mesure de portefeuille, pas un coût financier.

## 13. Démonstrateur adversarial

`python -m omega_value_os_t demo` contient quatre fixtures :

1. logiciel fortement cristallisé → éligible à revue humaine;
2. hypothèse très fertile mais faible en preuves → abstention/information;
3. action à forte utilité mais safety gate faux → bloquée;
4. revendication forte avec preuves faibles → bloquée par claim ceiling.

Les fixtures sont conçues pour empêcher deux régressions :

```text
HIGH VALUE != PERMISSION
HIGH AMBITION != HIGH CLAIM
```

## 14. Déterminisme et preuve logicielle

- JSON canonique trié;
- SHA-256 pour entrées et rapports;
- mêmes entrées → mêmes rapports;
- tests positifs et adversariaux;
- schémas JSON Draft 2020-12;
- workflow read-only;
- actions GitHub épinglées par SHA.

Un digest prouve l'identité des octets, pas la vérité du contenu.

## 15. Interfaces R0.1

```bash
python -m omega_value_os_t constitution
python -m omega_value_os_t oak
python -m omega_value_os_t demo
python -m omega_value_os_t evaluate case.json
python -m omega_value_os_t portfolio cases.json
```

Aucune commande `merge`, `publish`, `deploy`, `spend`, `file`, `send` ou `execute` n'existe.

## 16. OAK boundaries permanentes

```text
SCORE != PROBABILITY
PARETO != APPROVAL
CI GREEN != SCIENTIFIC VALIDATION
DIGEST != TRUTH
EXTERNAL USER != PRODUCT-MARKET FIT
REPEATED VALUE != GUARANTEED FUTURE VALUE
REVIEW ELIGIBLE != AUTHORIZED ACTION
AUTOMATION CAPABILITY != AUTOMATION AUTHORITY
HIGH UTILITY != SAFETY OVERRIDE
FERTILITY != CRYSTALLIZATION
```

## 17. R0.2 frontier

Priorités suivantes :

1. `ValueEvidence` typé avec provenance et dépendance entre preuves;
2. Confidence Debt temporelle et Uncertainty Half-Life;
3. registre M⁻ hash-chaîné + Anti-Repeat Gate;
4. Definition-of-Done compiler par type d'artefact;
5. WIP tokens et Expansion Freeze;
6. Time-to-Proof / Kill-Test planner;
7. Evidence Independence Graph;
8. Reality Distance calculée à partir de reçus externes;
9. interfaces `Claim`, `Evidence`, `Artifact`, `Experiment`, `Decision`, `Action`, `Product` partagées avec OAKGate/Rosette/Asset Factory;
10. méta-gouvernance : versionner et tester les politiques de valeurs elles-mêmes.

R0.2 devra préserver la propriété centrale de R0.1 : **aucun score ne peut accorder une autorité irréversible.**
