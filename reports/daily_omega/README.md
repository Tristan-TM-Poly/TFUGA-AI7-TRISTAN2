# Daily Ω Reports

This directory is reserved for generated Daily Ω Briefing and Daily Ω War Room reports.

## Report naming

```text
reports/daily_omega/YYYY-MM-DD.md
reports/daily_omega/YYYY-MM-DD.json
```

## Markdown report contract

```markdown
# Daily Ω War Room — YYYY-MM-DD

## Top 5 signals
1. Signal title
   - Source
   - OAK status
   - Canon branches
   - Prototype path
   - IP/revenue posture
   - Recommended issue

## Ω-CVCD synthesis
- Invariant of the day
- Best prototype candidate
- Best IP/revenue candidate
- Main M- warning
- One action today

## Memory updates
- M+
- M-

## Canon queue
- Seed
- Candidate
- Prototype
- Rejected
- Canon
```

## JSON report contract

JSON reports should follow `schemas/daily_omega_briefing.schema.json` and may include War Room routing metadata in optional fields.

## Promotion rule

A daily report should not be promoted to canon unless it includes:

- at least one credible source per selected item;
- OAK risk and falsification route;
- concrete next action;
- branch routing;
- IP/revenue posture where relevant.