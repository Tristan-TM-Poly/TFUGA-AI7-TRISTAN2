# Tristan Web OS — Gouvernance des données publiques

## Principe

Le site public ne doit pas être une copie totale du corpus privé. Il constitue une projection minimale, révisable et explicitement limitée.

```text
objet interne
→ classification
→ réduction publique
→ OAKGate
→ IPGate
→ PrivacyGate
→ SecurityGate
→ registre public
```

## Classes de visibilité

### `public-summary`

Résumé publiable contenant uniquement :

- définition générale;
- maturité;
- niveau de preuve déclaré;
- risques généraux;
- limite ou résultat négatif;
- prochaine action;
- source interne non sensible;
- liens de navigation.

### `partner`

Contenu destiné à un partenaire identifié et couvert par des règles d’accès. Non implémenté en R0.3.

### `private`

Notes, stratégies, données de travail, informations personnelles, hypothèses non réduites et journaux internes. Jamais inclus par défaut dans le générateur public.

### `ip-vault`

Inventions non publiées, analyses de brevetabilité, secrets commerciaux, plans détaillés, résultats sensibles et chronologie de conception. Jamais publié automatiquement.

## Données personnelles

R0.3 ne requiert aucun compte utilisateur et ne collecte aucune donnée personnelle.

Interdictions par défaut :

- dates et lieux de naissance détaillés;
- informations familiales;
- adresses;
- numéros de téléphone;
- dossiers scolaires ou médicaux;
- identifiants gouvernementaux;
- secrets d’authentification;
- données biométriques;
- historiques de navigation;
- télémétrie cachée.

Une information déjà connue dans le corpus ne devient pas publiable par simple présence dans un fichier interne.

## Propriété intellectuelle

Avant exposition publique, chaque objet doit être classé :

- publication ouverte;
- code open source;
- publication scientifique envisagée;
- brevet potentiel;
- secret commercial;
- licence partenaire;
- contenu tiers ou sous licence;
- statut incertain.

Le générateur public doit préférer un résumé abstrait lorsqu’un détail pourrait réduire la nouveauté brevetable, révéler un secret, violer une licence ou faciliter un usage risqué.

## Claims

Tout claim public doit conserver :

- identifiant stable;
- théorie source;
- type;
- statut;
- niveau épistémique;
- formulation;
- support déclaré;
- contre-hypothèse;
- limite ou falsification;
- prochain test;
- risques;
- interdiction de promotion automatique.

Un claim ne peut pas être promu uniquement parce que :

- son texte est cohérent;
- il apparaît dans plusieurs pages générées;
- il est relié à de nombreux nœuds;
- son score OAK est élevé;
- son nom est canonique;
- une simulation unique produit un motif intéressant.

## Relations

Les relations publiques sont limitées au rôle de navigation.

Elles peuvent signifier :

- documenté par;
- cartographié par;
- protégé par un garde d’incertitude;
- publié au travers de;
- utilisé comme composant;
- comparé à;
- généré depuis.

Elles ne doivent pas signifier implicitement :

- causalité;
- équivalence mathématique;
- identité physique;
- validation scientifique;
- propriété juridique;
- brevetabilité;
- sécurité;
- efficacité clinique;
- rendement financier.

## Scores OAK

Les six dimensions visibles sont :

- vérité;
- utilité;
- testabilité;
- simplicité;
- valeur;
- protection.

Ces nombres sont des signaux de navigation provisoires. Ils doivent être interprétés avec :

- provenance;
- méthode de calcul;
- date;
- domaine de validité;
- incertitude;
- historique de calibration;
- coût d’erreur.

R0.3 ne possède pas encore cette calibration complète. L’interface l’indique et interdit toute lecture probabiliste.

## Mémoire négative M⁻

M⁻ conserve :

- benchmark perdu;
- baseline supérieure;
- hypothèse réfutée;
- simulation instable;
- défaut de fabrication;
- absence de données;
- manque de validation externe;
- risque de surpromesse;
- contrainte réglementaire;
- échec d’intégration;
- coût excessif;
- action dangereuse ou irréversible.

Chaque entrée doit conduire à une règle anti-erreur ou à un chemin de récupération.

## Rétention et suppression

Le dépôt Git conserve l’historique. Une suppression publique doit donc distinguer :

1. retrait de l’interface;
2. retrait du registre courant;
3. réécriture d’historique exceptionnelle;
4. retrait d’un artefact de release;
5. invalidation d’un cache ou d’un déploiement.

Aucune réécriture destructive d’historique n’est autorisée automatiquement.

## Contributions

Une contribution modifiant le catalogue public doit :

- identifier la source;
- décrire le statut;
- ajouter ou maintenir une limite;
- fournir une prochaine action;
- respecter les quatre gates;
- préserver les identifiants existants;
- exécuter le générateur;
- exécuter l’audit;
- éviter toute donnée sensible;
- obtenir une révision humaine avant fusion.

## Incident de publication

Si un secret, une donnée personnelle ou un détail IP est exposé :

1. interrompre le déploiement;
2. retirer l’objet de la projection publique;
3. identifier tous les commits, caches, artefacts et forks concernés;
4. révoquer les secrets techniques si nécessaire;
5. documenter l’incident sans reproduire le contenu sensible;
6. consulter les responsables juridiques ou de sécurité appropriés;
7. ajouter une règle M⁻ empêchant la répétition.

Le simple retrait de la branche courante ne garantit pas l’effacement d’une information déjà publiée.
