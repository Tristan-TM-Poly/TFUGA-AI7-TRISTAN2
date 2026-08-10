"""Ω-NEURO-CELL-SYN-NET-T∞ — multiscale neuronal modeling kernel.

This package is research infrastructure. It separates established observations,
models, Tristan hypotheses, predictions, and evidence gaps; it is not a clinical
or diagnostic system.
"""

from .models import (
    DendriticBranchState,
    EpistemicStatus,
    HyperEdge,
    NetworkFingerprint,
    NeuroCellState,
    SynapseState,
)
from .dendrite import BranchIntegrator, SomaIntegrator
from .hypergraph import MultiscaleNeuroHypergraph
from .oakbench import ModelScore, OAKBench
from .synapse import effective_synaptic_weight, log_plasticity_update

__all__ = [
    "BranchIntegrator",
    "DendriticBranchState",
    "EpistemicStatus",
    "HyperEdge",
    "ModelScore",
    "MultiscaleNeuroHypergraph",
    "NetworkFingerprint",
    "NeuroCellState",
    "OAKBench",
    "SomaIntegrator",
    "SynapseState",
    "effective_synaptic_weight",
    "log_plasticity_update",
]

__version__ = "0.1.0"
