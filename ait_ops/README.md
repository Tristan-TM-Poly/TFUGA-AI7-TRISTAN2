# AIT-GitHubManager + AIT-CloudsServersManager v0.1

Double manager OAK-safe pour GitHub, clouds et serveurs.

## Mission

```text
Intent
→ OAK policy gate
→ GitHub plan
→ Cloud/server plan
→ runbook
→ dry-run commands
→ validation
→ PR/deploy gate
→ human approval
```

## GitHubManager

Prépare et gouverne repository scan, branch plan, commit plan, PR draft plan, review checklist, CI/checks gate, merge gate, release plan et issue/task plan.

## CloudsServersManager

Prépare et gouverne cloud inventory packet, server inventory packet, Docker/Kubernetes/systemd runbook, Terraform/Ansible skeleton packet, backup/rollback plan, cost/risk/security checklist et deploy gate.

## Bloqué par défaut

Secrets, SSH réel, cloud API réel, suppression serveur, modification DNS, exposition publique de ports, déploiement production, push direct main, historique réécrit, merge sans tests/CI/approval, commandes destructives.

## Résultat local

```text
ALL TESTS PASSED
OAK: ops_packet_ready_dry_run
GitHub: github_plan_ready_pr_draft
Cloud: cloud_plan_ready_dry_run
Files: 38
```

## OAK external action law

```text
external action allowed = explicit policy + human approval + least privilege + dry-run preview + tests green + rollback plan + audit log
```
