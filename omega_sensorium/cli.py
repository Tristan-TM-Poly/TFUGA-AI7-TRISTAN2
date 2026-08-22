from __future__ import annotations

import json
from dataclasses import asdict

from .compiler import MetaSensorium
from .models import Observable, ObservationCandidate, ScienceQuestion, SensorCapability


def example() -> None:
    sensorium = MetaSensorium()
    question = ScienceQuestion(
        question_id="Q-kilonova",
        statement="Discriminate two transient hypotheses with the smallest sufficient observation set",
        hypothesis_ids=("H-kilonova", "H-contaminant"),
        required_discrimination=0.8,
    )
    observables = (
        Observable("O-color", "optical/IR color evolution", "photometry", 0.6, 0.5, 0.8),
        Observable("O-spectrum", "spectral feature", "spectroscopy", 0.7, 0.7, 0.9),
    )
    sensors = (
        SensorCapability("S-wide", ("O-color",), 0.8, 0.7, 0.95, resource_cost=1.0, provenance=("example",)),
        SensorCapability("S-spec", ("O-spectrum",), 0.9, 0.9, 0.93, resource_cost=2.0, provenance=("example",)),
        SensorCapability("S-combo", ("O-color", "O-spectrum"), 0.9, 0.9, 0.90, resource_cost=4.0, provenance=("example",)),
    )
    genome = sensorium.science_to_sensor.compile(question, observables, sensors, provenance=("example",))
    candidates = (
        ObservationCandidate("C-fast", ("O-color",), ("S-wide",), 0.7, 0.75, 0.95, 0.8, resource_cost=1.0),
        ObservationCandidate("C-witness", ("O-spectrum",), ("S-spec",), 0.9, 0.9, 0.93, 0.9, resource_cost=2.0),
    )
    witness = sensorium.minimal_witness.select(
        candidates,
        min_discrimination=question.required_discrimination,
        min_calibration=0.8,
    )
    print(json.dumps({
        "observatory_genome": asdict(genome) if genome else None,
        "minimal_witness": asdict(witness) if witness else None,
        "new_meta_layer_needed": sensorium.should_create_new_meta_layer(
            verified_out_of_sample_gain=1.0,
            meta_complexity_cost=0.1,
            expressible_by_current_kernel=True,
        ),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    example()
