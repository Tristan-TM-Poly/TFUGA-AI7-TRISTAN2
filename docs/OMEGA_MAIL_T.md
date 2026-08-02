# Ω-MAIL-T R0.1 — Laboratoire de courriels intercompagnies de Tristan

## Statut

Prototype exécutable, déterministe et fermé. Il simule des communications entre compagnies synthétiques sous domaines réservés `.test`. Il ne fournit aucun transport réseau et ne doit pas être interprété comme une autorisation d'envoyer des courriels réels, commerciaux ou massifs.

## But

Transformer chaque conversation intercompagnies en test d'intégration vérifiable :

```text
CompanyGraph -> Scenario -> Message -> OAK-MailGate -> InMemoryTransport
             -> Mailbox -> Assertions -> Report -> M+ / M-
```

## Capacités R0.1

- compagnies et boîtes synthétiques;
- identités sous domaines `.test`;
- messages et fils déterministes;
- pièces jointes synthétiques typées;
- classification initiale par intention;
- scénario déclaratif au sous-ensemble JSON compatible YAML;
- assertions sur livraison, intention, classification, langue et pièces jointes;
- transport en mémoire seulement;
- blocage des destinataires inconnus, domaines externes et données non synthétiques;
- rapport JSON reproductible;
- CLI et tests pytest.

## Exécution

```bash
python -m omega_mail_t.cli run \
  scenarios/omega_mail_t/intercompany_support.yaml \
  --report reports/omega_mail_t/support-report.json

python examples/omega_mail_t_demo.py
python -m pytest tests/test_omega_mail_t.py
```

## Contrat OAK R0.1

Une livraison est autorisée seulement lorsque :

1. l'expéditeur et tous les destinataires sont enregistrés;
2. toutes les adresses utilisent un domaine `.test`;
3. la classification vaut `synthetic_internal`;
4. toutes les pièces jointes sont marquées synthétiques;
5. aucune livraison externe n'est demandée.

Toute violation produit `BLOCK` et un événement `DELIVERY_BLOCKED`.

## Limites connues

- pas de SMTP, IMAP, Gmail ou fournisseur réel;
- pas encore de CC/BCC distincts;
- pas encore de délais simulés ni de files persistantes;
- classification par règles simples, pas par modèle appris;
- le fichier `.yaml` utilise pour R0.1 le sous-ensemble JSON de YAML afin d'éviter une dépendance obligatoire;
- les assertions sémantiques avancées et la mémoire M− persistante restent à implémenter.

## Prochaines versions

### R0.2 — conversations et défaillances

Réponses, transferts, CC/BCC, ordre d'arrivée, délais, duplication, rebonds, quotas, retries et fils multi-agents.

### R0.3 — générateur de scénarios

Variation FR/EN, fuzzing contrôlé, cas contradictoires, pièces jointes factices et génération adaptative sans plafond arbitraire fixe.

### R0.4 — intégrations sandbox

Adaptateurs Mailpit/MailHog ou serveur SMTP de test, toujours derrière OAK-MailGate, liste blanche et arrêt d'urgence.

## Règle finale

Un courriel plausible n'est pas un test. Un scénario devient un test seulement lorsque son résultat attendu est explicitement vérifié et que toute sortie externe demeure bloquée par défaut.
