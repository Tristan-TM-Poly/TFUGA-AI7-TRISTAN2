# Ω-ACTION-EXT-T — Actions Externes et Automatisation Externe de Tristan

**Statut :** branche canonique/prototype MVP.  
**Principe :** automatiser l'action, jamais l'irresponsabilité.  
**Rôle :** transformer les intentions, théories, prototypes et décisions de Tristan en actions externes vérifiables, permissionnées, observables, réversibles quand possible, et apprenantes via M⁺/M⁻.

---

## 1. Définition

Une action externe est toute opération qui modifie un système hors du raisonnement interne : email, calendrier, Drive, GitHub, API, formulaire, paiement, CRM, cloud, institution, laboratoire, instrument ou système physique.

Une action externe canonique est représentée par :

```text
A = (Intent, Context, Permission, Risk, DryRun, Execution, Observation, Residue, Memory)
```

Une action n'est donc jamais un simple clic. C'est un objet traçable dans le HGFM.

---

## 2. Boucle canonique

```text
IntentGraph
  → Intent-to-Act Compiler
  → ActionDNA
  → Policy/Risk/IP/Legal/Safety Gates
  → DryRun Digital Twin
  → Human Approval when needed
  → Execution Kernel
  → Proof-of-Execution Ledger
  → Observation Loop
  → Rollback / Compensation
  → M⁺ / M⁻ / Canon update
```

Formule :

```text
Action_safe = Intent + Plan + Permission + DryRun + OAK + Approval + Execution + Observation + Residue + Memory
```

---

## 3. Niveaux d'autonomie

| Niveau | Nom | Autorisation |
|---|---|---|
| L0 | No action | Explication seulement |
| L1 | Draft only | Brouillons, manifests, dry-runs |
| L2 | Reversible safe action | Actions faibles risques avec rollback clair |
| L3 | Approved execution | Exécution après approbation explicite |
| L4 | Co-signed action | Tristan + expert / validation forte |
| L5 | Blocked | Action interdite ou trop risquée |

Règle : **ZERO-TOUCH maximal, mais jamais zéro-souveraineté.**

---

## 4. Tenseurs d'action

- **PermissionTensor** : qui peut faire quoi, où, quand, avec quelle portée.
- **RiskTensor** : légal, IP, financier, sécurité, vie privée, réputation, irréversibilité.
- **ConsentTensor** : consentement, pertinence, personnalisation, non-spam.
- **ReversibilityTensor** : rollback, compensation, backup, audit.
- **FertilityTensor** : utilité, apprentissage, revenu, réduction de friction, actif créé.
- **ProofTensor** : identifiant, timestamp, hash, observation, statut.
- **CostTensor** : temps, argent, énergie, réputation, maintenance, attention.
- **FragilityTensor** : API instable, permissions expirées, fuseaux horaires, secrets, erreurs humaines.
- **SovereigntyTensor** : visibilité, approbation, limites, arrêt d'urgence.

---

## 5. OAKGate externe

Décisions possibles :

```text
ALLOW_AUTO
ALLOW_DRAFT
NEEDS_APPROVAL
REQUIRE_EXPERT
BLOCK
```

Contraintes dures :

```text
PrivacyIncident = 0
SecretLeak = 0
IllegalAction = 0
UnauthorizedPayment = 0
UnapprovedPublicIPDisclosure = 0
```

---

## 6. Règles strictes

1. Une action qui touche l'argent, la loi, la santé, la sécurité, la réputation, l'IP, le public, les permissions ou des humains exige plus de simulation, d'approbation et de traçabilité.
2. Créer un brouillon est préférable à envoyer directement.
3. Créer une branche est préférable à modifier `main`.
4. Créer une PR draft est préférable à merger automatiquement.
5. Toute action publique liée à une invention doit passer par IP-Gate.
6. Toute action destructive exige backup, rollback ou compensation.
7. Toute action externe doit produire une preuve d'exécution ou une preuve de blocage.
8. Toute erreur devient M⁻ : incident, cause, anti-règle, test futur.

---

## 7. MVP GitHub actuel

Ce dossier ajoute un package `omega_action_ext_t` minimal avec :

- `ActionDNA` : représentation sérialisable d'une action.
- `RiskTensor` : scoring légal/IP/finance/safety/privacy/reputation/irreversibility.
- `OAKGate` : décision safe par règles explicites.
- `DryRunReport` : rapport avant exécution.
- `ProofOfExecution` : preuve append-only conceptuelle.
- tests anti-erreurs : email sans approbation → brouillon, IP publique → approbation, risque critique → expert, action réversible faible risque → auto.

---

## 8. Prochaine évolution

- Ajouter `ActionManifest.yaml` complet.
- Ajouter connecteurs GitHub/Gmail/Calendar/Drive en mode dry-run-first.
- Ajouter ledger JSONL append-only.
- Ajouter secret scanning avant commit/publication.
- Ajouter approval queue locale.
- Ajouter OAKBench d'actions externes.
- Ajouter M⁻ Incident Codex persistant.
