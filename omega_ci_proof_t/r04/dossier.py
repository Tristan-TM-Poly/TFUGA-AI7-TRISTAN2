from __future__ import annotations

from typing import Sequence

from .models import (
    BisectPlan,
    CausalDiagnosis,
    CausalDossier,
    CounterfactualWorld,
    DiscriminationPlan,
    ReproductionReceipt,
)


class CausalDossierBuilder:
    def build(
        self,
        diagnosis: CausalDiagnosis,
        discrimination_plan: DiscriminationPlan,
        reproduction: ReproductionReceipt,
        bisect_plan: BisectPlan,
        counterfactual_worlds: Sequence[CounterfactualWorld],
    ) -> CausalDossier:
        failure_ids = {
            diagnosis.failure_id,
            discrimination_plan.failure_id,
            reproduction.failure_id,
            bisect_plan.failure_id,
        }
        if len(failure_ids) != 1:
            raise ValueError("all dossier components must refer to the same failure")
        unresolved = []
        if diagnosis.status != "HEURISTICALLY_SUPPORTED":
            unresolved.append("leading cause remains ambiguous under the current observation model")
        if not reproduction.preserved_failure:
            unresolved.append("minimal reproduction does not preserve the failure")
        if bisect_plan.status != "BOUNDARY_IDENTIFIED":
            unresolved.append("first bad commit has not been identified")
        if not discrimination_plan.recommendations:
            unresolved.append("no safe discriminating experiment fits the declared budget")
        limitations = (
            "causal support is heuristic and model-relative",
            "counterfactual worlds are predictions, not observations",
            "bisect and experiments are plans only and are not executed",
            "unmodeled causes and interaction effects may remain",
        )
        return CausalDossier(
            failure_id=diagnosis.failure_id,
            diagnosis=diagnosis,
            discrimination_plan=discrimination_plan,
            reproduction=reproduction,
            bisect_plan=bisect_plan,
            counterfactual_worlds=tuple(counterfactual_worlds),
            unresolved_questions=tuple(unresolved),
            limitations=limitations,
        )
