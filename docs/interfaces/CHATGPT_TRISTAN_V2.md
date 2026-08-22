# Omega ChatGPT Tristan OS v2.4

Version v2.4 de l interface personnelle ChatGPT pour l ecosysteme Tristan.

## Vision

Transformer ChatGPT en operateur structure de l ecosysteme Tristan : mission, prompt compile, artifact intent, OAK card, M plus / M moins, HGFM local, presets GitHub, Data, Publications, Virtual Universities et export JSON.

## Emplacement

```text
interfaces/chatgpt-tristan-v2/
```

## Fonctionnalites

- Cockpit multi onglets : Composer, OAK, Memory, HGFM, GitHub, Data, Publications, v2.1-v2.4 et Export.
- Prompt compiler : compact, detailed, github-action, research-paper, oak-review, no-tools.
- OAK card editor et claims matrix.
- Memoire positive et negative locale.
- HGFM local avec export JSON et vue SVG simple.
- Presets GitHub Builder, Open Data Harvester, Publication Atlas.
- v2.4 Virtual Universities : generation locale de UniversityGenome, roster de Tristan Virtuels, simulation sandbox, fork, export JSON et prompt de compilation backend multijoueur.
- Contrat UniversityGenome dans `schemas/chatgpt-tristan/university_genome_contract.json`.
- Exemple dans `interfaces/chatgpt-tristan-v2/examples/virtual_university_genome.json`.
- Architecture canonique dans `docs/OMEGA_VIRTUAL_UNIVERSITIES_T.md`.
- Export session JSON et OAK cards.
- Contrats de validation dans schemas/chatgpt-tristan/.
- Exemples de sessions dans interfaces/chatgpt-tristan-v2/examples/.

## Lancer

```bash
python -m http.server 8000
```

Puis ouvrir :

```text
http://localhost:8000/interfaces/chatgpt-tristan-v2/
```

## Frontiere OAK

- Ce n est pas une modification officielle de ChatGPT.
- Ce n est pas un client API OpenAI.
- Ce n est pas un systeme d envoi automatique.
- Le cockpit v2.4 est un prototype local : il ne fournit pas encore un vrai multijoueur authentifie entre abonnes.
- Tous les Tristan Virtuels sont des agents IA/personas et non le Tristan humain.
- Simulation != Reality; Generated != Verified; Capability != Authority; Agent != Human.
- Les prompts generes doivent rester OAK-safe.
- Les actions externes exigent une revue humaine quand elles touchent contact, soumission, licence, securite, argent, permissions ou claims publics.

## Statut

- OAK-3 : architecture v2.4 definie.
- OAK-4 : interface locale executable, exemples, contrats, validateur CI.
- OAK-5 : apres backend multijoueur authentifie, stockage persistant, tests permissions/reconnexion et validation UX reelle avec plusieurs principals.
