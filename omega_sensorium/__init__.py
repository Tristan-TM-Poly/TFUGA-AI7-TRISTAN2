"""Ω Meta Sensorium Morphogenesis v1.

Proof-carrying reference primitives for science-to-sensor compilation, minimal-witness
selection, active observation, observation receipts, and regenerative observatory genomes.
"""

from .models import (
    ScienceQuestion,
    Observable,
    SensorCapability,
    DetectorGenome,
    ObservationCandidate,
    ObservatoryGenome,
    ObservationReceipt,
    SensoriumMemory,
)
from .compiler import (
    ReceiptGateResult,
    ScienceToSensorCompiler,
    MinimalWitnessCompiler,
    ActiveObservationEngine,
    ObservationCourt,
    MetaSensorium,
)

__all__ = [
    "ScienceQuestion",
    "Observable",
    "SensorCapability",
    "DetectorGenome",
    "ObservationCandidate",
    "ObservatoryGenome",
    "ObservationReceipt",
    "SensoriumMemory",
    "ReceiptGateResult",
    "ScienceToSensorCompiler",
    "MinimalWitnessCompiler",
    "ActiveObservationEngine",
    "ObservationCourt",
    "MetaSensorium",
]
