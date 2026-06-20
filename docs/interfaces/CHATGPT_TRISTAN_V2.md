# Omega ChatGPT Tristan OS v2

Version v2 de l interface personnelle ChatGPT pour l ecosysteme Tristan.

## Vision

Transformer ChatGPT en operateur structure de l ecosysteme Tristan : mission, prompt compile, artifact intent, OAK card, M plus / M moins, HGFM local, presets GitHub, Data, Publications et export JSON.

## Emplacement

```text
interfaces/chatgpt-tristan-v2/
```

## Fonctionnalites

- Cockpit multi onglets : Composer, OAK, Memory, HGFM, GitHub, Data, Publications, Export.
- Prompt compiler : compact, detailed, github-action, research-paper, oak-review, no-tools.
- OAK card editor et claims matrix.
- Memoire positive et negative locale.
- HGFM local avec export JSON et vue SVG simple.
- Presets GitHub Builder, Open Data Harvester, Publication Atlas.
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
- Les prompts generes doivent rester OAK-safe.
- Les actions externes exigent une revue humaine quand elles touchent contact, soumission, licence, securite ou claims publics.

## Statut

- OAK-3 : architecture v2 definie.
- OAK-4 : interface executable, exemples, contrats, validateur CI.
- OAK-5 : apres test UX reel et correction des sessions.
