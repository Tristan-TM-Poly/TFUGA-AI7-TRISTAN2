# Ω-PLASMA-T∞

Noyau Python sans dépendance obligatoire pour classifier un état plasma, calculer ses échelles, compiler les modèles candidats, auditer les hypothèses OAK, explorer des atlas et générer des campagnes paramétriques sans plafond architectural fixe.

## Exécution

```bash
python -m omega_plasma_t.cli assess examples/omega_plasma_state.json --output-dir generated/plasma
python -m omega_plasma_t.cli atlas tearing
python -m omega_plasma_t.cli campaign examples/omega_plasma_campaign.json --output generated/plasma/campaign.jsonl
python -m pytest tests/test_omega_plasma_*.py -q
```

## Portée

Le paquet couvre le noyau commun: état typé, longueurs/fréquences caractéristiques, classification multi-label, compilation explicable des modèles, dispersion analytique de base, réseau réactionnel, hypergraphe, topologie, OAKGate, rapports et campagnes. Il ne prétend pas remplacer un solveur PIC, MHD, gyrocinétique, quantique ou radiatif de production.

## Invariant de sécurité

Aucune sortie n'autorise automatiquement une expérience, un appareil haute tension, un laser, un système sous vide, une source de rayonnement, un réacteur, un propulseur ou une commande matérielle.
