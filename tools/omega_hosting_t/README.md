# Ω-HOSTING-T Tools

## `oak_hosting_gate.py`

Prototype de scoring OAK sans dépendances externes.

Il ne déploie rien. Il décide si un composant devrait aller vers :

- Hostinger Web/Cloud ;
- Hostinger VPS ;
- Vercel/Cloudflare ;
- Supabase/Postgres ;
- compute GPU dédié ;
- blocage jusqu'à revue.

## Exemples

Landing page publique avec rollback :

```bash
python tools/omega_hosting_t/oak_hosting_gate.py \
  --component-type landing_page \
  --asset-class public_marketing \
  --public-exposure true \
  --rollback-defined true
```

n8n VPS avec état, backups, rollback et approval gate :

```bash
python tools/omega_hosting_t/oak_hosting_gate.py \
  --component-type n8n \
  --asset-class public_marketing \
  --stores-state true \
  --uses-external-actions true \
  --rollback-defined true \
  --backups-defined true \
  --human-approval-gate true
```

Blocage attendu pour secrets ou IP non revue :

```bash
python tools/omega_hosting_t/oak_hosting_gate.py \
  --component-type landing_page \
  --asset-class confidential_ip \
  --public-exposure true \
  --reveals-unreviewed-ip true
```

## Règle Tristan

Le score n'est pas une vérité. C'est un garde-fou anti-surconfiance. Une décision réelle doit inclure :

- classification ;
- preuve ;
- rollback ;
- revue humaine si risque sensible ;
- mémoire M⁻ en cas d'incident.
