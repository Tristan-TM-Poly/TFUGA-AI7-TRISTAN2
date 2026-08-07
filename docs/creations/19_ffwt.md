# FFWT — Fast Fractal Wavelet Transform

## Vision

FFWT cherche à enrichir l’analyse en ondelettes par des informations de fractalité, de persistance et d’auto-similarité. La méthode sélectionne ou pondère les coefficients selon leur fertilité multi-échelle.

## Applications

- signaux fractals;
- spectroscopie;
- anomalies et textures;
- débruitage;
- compression;
- classification.

## Résultat négatif important

Une première pondération fractale naïve a produit une reconstruction moins précise qu’une FWT classique. Ce résultat a été conservé dans M⁻.

## Produit potentiel

Une bibliothèque expérimentale de transformations fractales avec benchmarks, visualisations et registre des variantes échouées.

## Statut OAK

Prototype réel; supériorité non démontrée.

## Prochaine preuve

Tester FFWT sur des tâches où la fractalité peut apporter une information discriminante, notamment la détection d’anomalies ou la classification, plutôt que sur la reconstruction seule.
