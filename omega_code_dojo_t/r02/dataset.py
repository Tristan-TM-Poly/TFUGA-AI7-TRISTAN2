from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .hashing import sha256_hex, stable_id
from .models import TaskIR


@dataclass(frozen=True)
class DatasetRecord:
    record_id: str
    record_type: str
    task_id: str
    input_payload: dict[str, Any]
    target_payload: dict[str, Any]
    provenance_hash: str
    license_id: str
    evidence_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "task_id": self.task_id,
            "input_payload": self.input_payload,
            "target_payload": self.target_payload,
            "provenance_hash": self.provenance_hash,
            "license_id": self.license_id,
            "evidence_status": self.evidence_status,
        }


@dataclass(frozen=True)
class DatasetManifest:
    dataset_id: str
    record_type: str
    record_count: int
    records_sha256: str
    licenses: tuple[str, ...]
    training_allowed: bool
    records: tuple[DatasetRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "record_type": self.record_type,
            "record_count": self.record_count,
            "records_sha256": self.records_sha256,
            "licenses": list(self.licenses),
            "training_allowed": self.training_allowed,
            "records": [record.to_dict() for record in self.records],
        }


class DatasetCompiler:
    supported_types = frozenset({"sft", "preference", "critique", "proof", "translation"})

    def compile_task_ir(
        self,
        tasks: Iterable[TaskIR],
        record_type: str = "sft",
    ) -> DatasetManifest:
        if record_type not in self.supported_types:
            raise ValueError(f"unsupported record type: {record_type}")
        records: list[DatasetRecord] = []
        for task in tasks:
            if not task.provenance.training_allowed:
                raise PermissionError(
                    f"task {task.task_id} is not authorized for training datasets"
                )
            input_payload = {
                "title": task.title,
                "statement": task.statement,
                "input_schema": dict(task.input_schema),
                "output_schema": dict(task.output_schema),
                "constraints": [item.to_dict() for item in task.constraints],
            }
            target_payload = self._target_for(task, record_type)
            record_id = stable_id(
                "dataset-record",
                [record_type, task.task_id, input_payload, target_payload],
                length=20,
            )
            records.append(
                DatasetRecord(
                    record_id=record_id,
                    record_type=record_type,
                    task_id=task.task_id,
                    input_payload=input_payload,
                    target_payload=target_payload,
                    provenance_hash=task.provenance.content_hash,
                    license_id=task.provenance.license_id,
                    evidence_status=task.evidence_status.value,
                )
            )
        records.sort(key=lambda record: record.record_id)
        payload = [record.to_dict() for record in records]
        records_hash = sha256_hex(payload)
        licenses = tuple(sorted({record.license_id for record in records}))
        dataset_id = stable_id(
            "dataset",
            [record_type, records_hash, licenses],
            length=20,
        )
        return DatasetManifest(
            dataset_id=dataset_id,
            record_type=record_type,
            record_count=len(records),
            records_sha256=records_hash,
            licenses=licenses,
            training_allowed=True,
            records=tuple(records),
        )

    @staticmethod
    def _target_for(task: TaskIR, record_type: str) -> dict[str, Any]:
        if record_type == "sft":
            return {
                "task_ir": task.to_dict(),
                "required_invariants": list(task.invariants),
            }
        if record_type == "preference":
            return {
                "preferred_properties": [
                    "correctness",
                    "mutation resistance",
                    "explicit complexity",
                    "boundary robustness",
                ],
                "rejected_properties": list(task.forbidden_assumptions),
            }
        if record_type == "critique":
            return {
                "questions": [
                    "Which assumptions are unproven?",
                    "Which mutation family can survive?",
                    "What is the smallest counterexample?",
                ],
                "forbidden_assumptions": list(task.forbidden_assumptions),
            }
        if record_type == "proof":
            return {
                "invariants": list(task.invariants),
                "proof_obligations": [
                    "partial correctness",
                    "termination",
                    "complexity bound",
                ],
            }
        return {
            "algorithm_ir": task.task_id,
            "target_languages": list(task.tags),
            "equivalence_obligations": [
                "numeric semantics",
                "iteration order",
                "exception behavior",
            ],
        }
