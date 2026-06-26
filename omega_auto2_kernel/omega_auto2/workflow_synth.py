from __future__ import annotations

import re

from .models import Workflow


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug[:64] or "generated_workflow"


def infer_steps(task_description: str) -> list[str]:
    text = task_description.lower()
    steps = ["collect_inputs", "deduplicate", "structure_task"]

    if any(word in text for word in ["papier", "paper", "article", "scientifique"]):
        steps += ["summarize_sources", "extract_claims", "classify_evidence", "run_scientific_oak_check"]
    elif any(word in text for word in ["github", "dépôt", "repo", "code"]):
        steps += ["generate_repo_structure", "write_readme", "write_tests", "prepare_pull_request_draft"]
    elif any(word in text for word in ["revenu", "business", "client", "vente"]):
        steps += ["extract_offer", "identify_customer_segment", "score_market_risk", "draft_next_action"]
    elif any(word in text for word in ["drive", "fichier", "document"]):
        steps += ["scan_files", "hash_outputs", "detect_duplicates", "draft_reorganization_plan"]
    else:
        steps += ["extract_invariants", "generate_workflow_dna", "run_oak_check"]

    return steps + ["produce_dry_run_report", "log_to_m_plus_m_minus"]


def forge_workflow_from_task(task_description: str, *, owner: str = "Tristan") -> Workflow:
    workflow_id = _slugify(task_description)
    return Workflow(
        id=f"auto2_{workflow_id}",
        name=f"AUTO² Forge: {task_description[:48]}",
        owner=owner,
        purpose=f"Transformer la tâche suivante en workflow OAK-safe: {task_description}",
        trigger={"type": "manual", "schedule": "on_demand"},
        inputs=["task_description", "user_constraints", "available_tools"],
        steps=infer_steps(task_description),
        outputs=["workflow_yaml", "oak_report", "next_action"],
        permissions={
            "read": ["local_context", "user_instruction"],
            "write": ["local_draft"],
            "forbidden": [
                "delete_files",
                "public_publish",
                "external_email",
                "spend_money",
                "change_permissions",
                "ip_disclosure",
            ],
        },
        oak={
            "required": True,
            "checks": [
                "clarity",
                "safety",
                "reversibility",
                "least_privilege",
                "cost_control",
                "ip_and_legal_risk",
                "human_approval_for_sensitive_actions",
            ],
        },
    )
