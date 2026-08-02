# Canon Ω-RE-T∞ R0.1

## Règle centrale

Le reverse engineering de Tristan reconstruit l’espace des mécanismes compatibles avec des observations autorisées. Il cherche ensuite les expériences réversibles qui réduisent cet espace sans confondre équivalence comportementale et identité interne.

## Invariants

1. Toute campagne possède un périmètre d’autorisation explicite.
2. Toute observation importante possède une provenance.
3. Une inférence n’est jamais enregistrée comme observation.
4. Une fidélité comportementale élevée ne prouve pas l’identité interne.
5. Les mécanismes indiscernables restent dans une même classe d’équivalence.
6. Tout contre-exemple est conservé dans la mémoire négative.
7. La promotion `VERIFIED` exige une validation indépendante.
8. Une spécification clean-room décrit le comportement sans reprendre une implémentation inaccessible.
9. Les risques légaux, humains et techniques réduisent l’utilité d’une expérience.
10. Le système échoue fermé lorsque l’autorisation ou la provenance est insuffisante.

## Équation canonique

\[
a^*=\arg\max_a \left[\mathbb{E}(\Delta I\mid a)-\lambda_C C(a)-\lambda_R R(a)-\lambda_L L(a)\right]
\]

## Artefacts obligatoires

- `AuthorizationScope`;
- `EvidenceLedger`;
- observations brutes;
- population ou générateur d’hypothèses;
- posterior;
- expériences discriminantes;
- dette d’identifiabilité;
- jumeau contrefactuel;
- rapport OAK;
- spécification clean-room;
- registre M⁻ des échecs et contre-exemples.
