from __future__ import annotations

from typing import Mapping, Sequence

from .models import CausalHypothesis, CounterfactualWorld, ExperimentDesign


class CounterfactualProjector:
    def project(
        self,
        hypotheses: Sequence[CausalHypothesis],
        experiment: ExperimentDesign,
    ) -> tuple[CounterfactualWorld, ...]:
        by_id = {item.hypothesis_id: item for item in hypotheses}
        if set(experiment.likelihoods) != set(by_id):
            raise KeyError("experiment must define outcomes for every modeled hypothesis")
        return tuple(
            CounterfactualWorld(
                hypothesis_id=hypothesis_id,
                intervention=experiment.experiment_id,
                predicted_outcomes=dict(experiment.likelihoods[hypothesis_id]),
                assumptions=by_id[hypothesis_id].assumptions,
            )
            for hypothesis_id in sorted(by_id)
        )
