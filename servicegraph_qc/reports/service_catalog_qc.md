# Catalogue prioritaire Ω-SERVICES-QC-T

Ce catalogue sert à choisir les prochains ServiceGraphs à modéliser. La priorité est donnée aux services où un délai, une erreur ou un manque de clarté peut créer un impact humain, financier, éducatif ou administratif important.

## Niveau critique

1. Santé : référence vers spécialiste et suivi de rendez-vous.
2. RAMQ : carte d'assurance maladie, admissibilité et renouvellement.
3. Soutien du revenu : demande, preuve, versements et révision.
4. Justice : petites créances, logement, famille et suivi de dossier.
5. Immigration : statut, documents, francisation, reconnaissance des compétences.
6. Revenu Québec : avis, paiement, correction, opposition, travailleurs autonomes.
7. SAAQ : permis, immatriculation, dossier conducteur, rendez-vous.
8. Travail : accident, indemnisation, retour au travail.
9. Logement : plainte, audience, salubrité et suivi administratif.
10. Transport adapté : admissibilité, réservation, annulation, retards.

## Niveau élevé

11. Aide financière aux études.
12. Admission formation professionnelle, cégep ou université.
13. Services aux entreprises : démarrage, immatriculation, taxes, permis.
14. Permis municipaux : construction, rénovation, zonage.
15. Garderies : inscription, subventions, place, changement familial.
16. Retraite Québec : rente, invalidité, décès et proches aidants.
17. Élections Québec : changement d'adresse, inscription, accessibilité.
18. Services régionaux : accès en région éloignée et faible connectivité.
19. Permis environnementaux pour citoyens et PME.
20. Hydro et énergie : branchements, pannes, programmes d'efficacité.

## Plateformes transversales

- Identité numérique et authentification.
- Changement d'adresse unique.
- Paiement gouvernemental commun.
- Statut de demande universel.
- Notifications et rappels consentis.
- Coffre citoyen de documents avec consentement.
- Tableau de bord des délais publics.
- Registre M moins des fiascos et règles anti-répétition.
- Laboratoire citoyen et employés publics.
- OAKGate gouvernemental avant déploiement massif.

## Méthode de sélection

Un service reçoit une priorité forte si au moins trois conditions sont vraies :

- délai long ou imprévisible;
- conséquence importante pour citoyen ou PME;
- multiples portails ou organismes;
- documents redemandés;
- faible transparence de statut;
- canaux humains insuffisants;
- forte dépendance fournisseur;
- historique de panne ou échec;
- populations vulnérables touchées;
- coût public élevé ou mal visible.

## Sortie par service

Chaque service prioritaire doit produire :

```text
1. ServiceGraph YAML
2. FrictionMap
3. OAK-ServiceMeter score
4. mémoire négative anti-erreurs
5. tests citoyens et employés
6. recommandations de simplification
7. mode dégradé et rollback
8. tableau de bord public minimal
```
