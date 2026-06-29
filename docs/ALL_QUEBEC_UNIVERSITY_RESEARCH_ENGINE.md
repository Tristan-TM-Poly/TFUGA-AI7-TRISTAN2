# All Quebec University Research Engine

## Mission

Automate research-contact discovery, route scoring, message adaptation, execution tracking, and follow-up for every Quebec university and the BCI.

## Operating rule

```text
No guessed emails. No mass sending. No unsupported claims. Every contact route must be official or marked pending.
```

## Coverage

```text
18 Quebec universities + BCI interuniversity route
```

## Files

| File | Role |
|---|---|
| `all_university_research_engine.yaml` | full matrix of universities, status, research angles, next actions |
| `research_contact_discovery_protocol.yaml` | official route discovery and scoring protocol |

## Status model

| Status | Meaning |
|---|---|
| GREEN_EMAIL_SENT | verified email was sent and Gmail proof recorded |
| GREEN_EMAIL_READY | verified email is ready but not sent |
| GREEN_FORM_READY | official form route is verified; submission requires form confirmation |
| TO_DISCOVER | route/contact not yet researched deeply |
| YELLOW | official route exists but needs more precise contact |
| RED | rejected route; guessed/unofficial/stale |

## Research-axis model

Each university receives a research-angle vector such as:

```text
AI / scientific AI / energy / materials / datacenters / batteries / nonlinear systems / optimization / regional innovation / governance / learning systems / technology transfer / patents
```

## Automation loop

```text
Discover -> Score -> Adapt -> Send or Packet -> Record -> Monitor -> Follow-up -> M+/M-
```

## OAK rule

```text
A university becomes green only by verified email send or verified official-form route. Anything else remains pending.
```
