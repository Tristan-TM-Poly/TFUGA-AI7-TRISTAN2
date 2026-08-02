from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import prod
from pathlib import Path
from time import perf_counter
from typing import Any, Iterator, Mapping, Sequence

from .genome import FluidGenome


@dataclass(frozen=True)
class FrontierAxis:
    name: str
    values: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name or not self.values:
            raise ValueError("frontier axes require a name and at least one value")
        if len(set(self.values)) != len(self.values):
            raise ValueError(f"axis {self.name!r} contains duplicate values")


@dataclass(frozen=True)
class FrontierPlan:
    start: int
    count: int
    epoch_start: int
    epoch_end: int
    local_cardinality: int
    virtual_cardinality: str
    estimated_jsonl_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start,
            "count": self.count,
            "end_exclusive": self.start + self.count,
            "epoch_start": self.epoch_start,
            "epoch_end": self.epoch_end,
            "local_cardinality": self.local_cardinality,
            "virtual_cardinality": self.virtual_cardinality,
            "estimated_jsonl_bytes": self.estimated_jsonl_bytes,
            "permanent_total_cap": None,
            "boundary": "Each run is finite and resource-bounded; the epoch-indexed address space has no fixed total-record ceiling.",
        }


class FluidFrontierSpace:
    """Mixed-radix, epoch-indexed fluid-object address space.

    One epoch enumerates the Cartesian product of the ontology axes. Global
    non-negative indices add an unbounded epoch coordinate, so no permanent
    total-addition cap is encoded in the generator.
    """

    def __init__(self, axes: Sequence[FrontierAxis]) -> None:
        if not axes:
            raise ValueError("at least one frontier axis is required")
        if len({axis.name for axis in axes}) != len(axes):
            raise ValueError("axis names must be unique")
        self.axes = tuple(axes)
        self.local_cardinality = prod(len(axis.values) for axis in self.axes)

    def plan(self, *, start: int, count: int, estimated_bytes_per_record: int = 900) -> FrontierPlan:
        if start < 0 or count < 0:
            raise ValueError("start and count must be non-negative")
        end_index = start if count == 0 else start + count - 1
        return FrontierPlan(
            start=start,
            count=count,
            epoch_start=start // self.local_cardinality,
            epoch_end=end_index // self.local_cardinality,
            local_cardinality=self.local_cardinality,
            virtual_cardinality="countably_unbounded_by_epoch",
            estimated_jsonl_bytes=count * estimated_bytes_per_record,
        )

    def decode(self, global_index: int) -> tuple[int, int, dict[str, str]]:
        if global_index < 0:
            raise ValueError("global_index must be non-negative")
        epoch, remainder = divmod(global_index, self.local_cardinality)
        coordinates: dict[str, str] = {}
        for axis in reversed(self.axes):
            remainder, offset = divmod(remainder, len(axis.values))
            coordinates[axis.name] = axis.values[offset]
        coordinates = {axis.name: coordinates[axis.name] for axis in self.axes}
        return epoch, global_index % self.local_cardinality, coordinates

    def genome(self, global_index: int) -> FluidGenome:
        epoch, local_index, c = self.decode(global_index)
        stable_id = f"omega-fluid-e{epoch:08d}-i{local_index:016d}"
        return FluidGenome(
            genome_id=stable_id,
            fluid_family=c["fluid_family"],
            regime=c["regime"],
            phenomenon=c["phenomenon"],
            geometry=c["geometry"],
            boundary=c["boundary"],
            solver=c["solver"],
            scale=c["scale"],
            object_type=c["object_type"],
            uncertainty_class=c["uncertainty"],
            evidence_status=c["evidence_status"],
            assumptions=(
                "Generated research cell; not an empirical discovery.",
                "Units, constitutive laws and validation must be supplied before promotion.",
            ),
            provenance={
                "generator": "omega_fluid_t.frontier.FluidFrontierSpace",
                "global_index": global_index,
                "ontology_axes": len(self.axes),
            },
            epoch=epoch,
            local_index=local_index,
        )

    def iter_genomes(self, *, start: int = 0, count: int) -> Iterator[FluidGenome]:
        if start < 0 or count < 0:
            raise ValueError("start and count must be non-negative")
        for global_index in range(start, start + count):
            yield self.genome(global_index)


@dataclass(frozen=True)
class WriterPolicy:
    target_shard_bytes: int = 8 * 1024 * 1024
    checkpoint_interval: int = 10_000
    fsync: bool = False

    def __post_init__(self) -> None:
        if self.target_shard_bytes <= 0 or self.checkpoint_interval <= 0:
            raise ValueError("writer policy values must be positive")


class FrontierWriter:
    def __init__(self, output_dir: str | Path, *, policy: WriterPolicy | None = None) -> None:
        self.output_dir = Path(output_dir)
        self.policy = policy or WriterPolicy()

    def materialize(self, space: FluidFrontierSpace, *, start: int, count: int) -> dict[str, Any]:
        if start < 0 or count < 0:
            raise ValueError("start and count must be non-negative")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        shard_dir = self.output_dir / "shards"
        shard_dir.mkdir(exist_ok=True)
        checkpoint_path = self.output_dir / "checkpoint.json"
        manifest_path = self.output_dir / "manifest.json"

        checkpoint = self._load_checkpoint(checkpoint_path)
        expected_start = int(checkpoint.get("next_index", start))
        if checkpoint and expected_start < start:
            raise ValueError("checkpoint precedes the requested start; use a clean output directory")
        current_index = max(start, expected_start)
        requested_end = start + count
        if current_index > requested_end:
            raise ValueError("checkpoint is beyond the requested range")

        previous_digest = str(checkpoint.get("chain_digest", "0" * 64))
        accepted = current_index - start
        shard_number = int(checkpoint.get("next_shard", 0))
        started = perf_counter()

        while current_index < requested_end:
            shard_path = shard_dir / f"fluid-{shard_number:08d}.jsonl"
            shard_bytes = 0
            with shard_path.open("w", encoding="utf-8") as handle:
                while current_index < requested_end and shard_bytes < self.policy.target_shard_bytes:
                    genome = space.genome(current_index)
                    record = genome.to_dict()
                    record["global_index"] = current_index
                    record["content_hash"] = genome.content_hash()
                    record["previous_chain_digest"] = previous_digest
                    chain_material = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                    previous_digest = sha256((previous_digest + chain_material).encode("utf-8")).hexdigest()
                    record["chain_digest"] = previous_digest
                    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                    handle.write(line)
                    shard_bytes += len(line.encode("utf-8"))
                    accepted += 1
                    current_index += 1
                    if accepted % self.policy.checkpoint_interval == 0:
                        self._write_checkpoint(
                            checkpoint_path,
                            next_index=current_index,
                            next_shard=shard_number + 1,
                            accepted=accepted,
                            chain_digest=previous_digest,
                        )
                handle.flush()
                if self.policy.fsync:
                    import os
                    os.fsync(handle.fileno())
            shard_number += 1
            self._write_checkpoint(
                checkpoint_path,
                next_index=current_index,
                next_shard=shard_number,
                accepted=accepted,
                chain_digest=previous_digest,
            )

        elapsed = perf_counter() - started
        manifest = {
            **space.plan(start=start, count=count).to_dict(),
            "accepted": accepted,
            "resumed_from": expected_start if checkpoint else None,
            "next_index": current_index,
            "shards": shard_number,
            "chain_digest": previous_digest,
            "elapsed_seconds": elapsed,
            "throughput_records_per_second": accepted / max(elapsed, 1e-12),
            "duplicate_ids": 0,
            "source_mutations": 0,
            "remote_mutations": 0,
            "oak_status": "GENERATED_RESEARCH_CELLS_NOT_SCIENTIFIC_DISCOVERIES",
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return manifest

    @staticmethod
    def _load_checkpoint(path: Path) -> Mapping[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_checkpoint(path: Path, **payload: Any) -> None:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)


def default_fluid_space() -> FluidFrontierSpace:
    axes = (
        FrontierAxis("fluid_family", (
            "liquid", "gas", "plasma", "supercritical", "polymer_melt", "suspension", "emulsion", "foam",
            "gel", "granular_flow", "blood", "mucus", "cytoplasm", "active_matter", "ocean", "atmosphere",
            "river", "magma", "glacier", "porous_multiphase", "superfluid", "bose_einstein_condensate", "electron_fluid", "relativistic_fluid",
            "reactive_mixture", "combustion_products", "cryogenic_fluid", "nanofluid", "ferrofluid", "electrolyte", "slurry", "unknown_candidate",
        )),
        FrontierAxis("regime", (
            "stokes", "laminar", "transitional", "turbulent", "incompressible", "weakly_compressible", "compressible", "hypersonic",
            "continuum", "slip_flow", "transitional_knudsen", "free_molecular", "newtonian", "shear_thinning", "shear_thickening", "viscoelastic",
            "yield_stress", "thixotropic", "rotating", "stratified", "magnetohydrodynamic", "relativistic", "quantum", "multiphase",
        )),
        FrontierAxis("phenomenon", (
            "advection", "diffusion", "convection", "shear", "boundary_layer", "separation", "vortex_shedding", "mixing",
            "kelvin_helmholtz", "rayleigh_taylor", "richtmyer_meshkov", "rayleigh_benard", "marangoni", "taylor_couette", "rayleigh_plateau", "shock",
            "rarefaction", "detonation", "deflagration", "cavitation", "boiling", "condensation", "evaporation", "nucleation",
            "coalescence", "breakup", "porous_transport", "fluid_structure_interaction", "electrohydrodynamics", "magnetohydrodynamics", "wave_propagation", "unknown_instability",
        )),
        FrontierAxis("geometry", (
            "channel", "pipe", "cavity", "cylinder", "sphere", "airfoil", "jet", "wake",
            "mixing_layer", "nozzle", "diffuser", "porous_medium", "fracture_network", "vascular_tree", "microchannel", "droplet",
            "bubble", "thin_film", "free_surface", "rotating_annulus", "hexagonal_fractal_channel", "mycelial_network", "unstructured_domain", "unknown_geometry",
        )),
        FrontierAxis("boundary", (
            "no_slip", "free_slip", "navier_slip", "inflow_velocity", "outflow_pressure", "periodic", "symmetry", "moving_wall",
            "adiabatic", "isothermal", "heat_flux", "reactive_wall", "porous_wall", "permeable_membrane", "charged_wall", "magnetic_boundary",
            "deforming_interface", "immersed_boundary", "rough_wall", "hydrophobic_wall", "hydrophilic_wall", "open_boundary", "radiative_boundary", "unknown_boundary",
        )),
        FrontierAxis("solver", (
            "finite_difference", "finite_volume", "finite_element", "spectral", "pseudo_spectral", "discontinuous_galerkin", "lattice_boltzmann", "sph",
            "vortex_method", "level_set", "volume_of_fluid", "phase_field", "immersed_boundary", "boundary_element", "particle_in_cell", "kinetic_boltzmann",
            "hybrid_continuum_kinetic", "reduced_order_model", "neural_operator_guarded", "symbolic_solver",
        )),
        FrontierAxis("uncertainty", (
            "initial_condition", "boundary_condition", "material_parameter", "closure_model", "numerical_discretization", "measurement_noise", "model_form", "geometry",
            "phase_topology", "reaction_kinetics", "scale_bridge", "solver_tolerance", "data_shift", "unknown_unknown", "combined", "none_declared",
        )),
        FrontierAxis("scale", (
            "quantum", "molecular", "kinetic", "mesoscopic", "microfluidic", "laboratory", "device", "industrial", "geophysical", "planetary", "astrophysical", "multiscale",
        )),
        FrontierAxis("evidence_status", (
            "IDEA", "FORMALIZED", "IMPLEMENTED", "TESTED", "BENCHMARKED", "SIMULATED", "MEASURED", "REFUTED", "ARCHIVED", "CERTIFIED_COMPUTATIONAL",
        )),
        FrontierAxis("object_type", (
            "CLAIM", "EQUATION", "MODEL", "SOLVER", "TEST", "BENCHMARK", "COUNTEREXAMPLE", "RISK",
            "M_MINUS", "M_PLUS", "EXPERIMENT", "GEOMETRY", "BOUNDARY", "CLOSURE", "PRODUCT_CANDIDATE", "PUBLICATION_CANDIDATE",
        )),
    )
    return FluidFrontierSpace(axes)
