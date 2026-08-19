from __future__ import annotations

from dataclasses import replace

from ..certificate import build_certificate, verify_certificate
from ..models import CandidateStatus, PrimeCandidate
from ..primality import is_prime
from ..proth import prove_proth
from ..sieve import screen_candidate
from .models import CampaignManifest, CampaignSummary, TaskReceipt, TaskState
from .registry import LocalPrimeRegistry
from .storage import CampaignStore


class CampaignEngine:
    def __init__(self, store: CampaignStore, *, sieve_bound: int = 10_000):
        if sieve_bound < 2:
            raise ValueError("sieve_bound must be >= 2")
        self.store = store
        self.sieve_bound = sieve_bound

    def execute(
        self,
        manifest: CampaignManifest,
        *,
        max_tasks: int | None = None,
    ) -> CampaignSummary:
        self.store.load_manifest(manifest)
        summary = CampaignSummary(campaign_id=manifest.campaign_id, planned=manifest.task_count)
        registry = LocalPrimeRegistry(self.store)
        for task in list(self.store.iter_pending(manifest.campaign_id, limit=max_tasks)):
            summary.processed += 1
            candidate = PrimeCandidate(
                value=task.value,
                family=task.family,
                parameters={"k": task.k, "n": task.exponent, "expression": f"{task.k}*2^{task.exponent}+1"},
            )
            try:
                screened = screen_candidate(candidate, self.sieve_bound)
                if screened.status is CandidateStatus.FILTERED_COMPOSITE:
                    summary.filtered_composites += 1
                    self.store.update_task(task, TaskState.FILTERED_COMPOSITE, factor=screened.small_factor)
                    summary.receipts.append(
                        TaskReceipt(task.task_id, TaskState.FILTERED_COMPOSITE, str(task.value), factor=screened.small_factor)
                    )
                    continue
                if not is_prime(task.value):
                    summary.composites += 1
                    self.store.update_task(task, TaskState.COMPOSITE)
                    summary.receipts.append(TaskReceipt(task.task_id, TaskState.COMPOSITE, str(task.value)))
                    continue
                summary.probable_primes += 1
                proof = prove_proth(task.value)
                if proof is None:
                    self.store.update_task(task, TaskState.PROBABLE_PRIME)
                    summary.receipts.append(TaskReceipt(task.task_id, TaskState.PROBABLE_PRIME, str(task.value)))
                    continue
                summary.proven_primes += 1
                proven = replace(candidate, status=CandidateStatus.PROVEN_PRIME, witness=proof.witness)
                certificate = build_certificate(
                    proven,
                    proof,
                    timestamp_utc="1970-01-01T00:00:00+00:00",
                    software_commit="r02-deterministic-fixture",
                ).to_dict()
                valid, errors = verify_certificate(certificate)
                if not valid:
                    raise RuntimeError("; ".join(errors))
                self.store.update_task(task, TaskState.CERTIFIED, certificate=certificate)
                registry.register(manifest.campaign_id, certificate)
                summary.certified += 1
                summary.receipts.append(
                    TaskReceipt(
                        task.task_id,
                        TaskState.CERTIFIED,
                        str(task.value),
                        certificate_id=certificate["certificate_id"],
                        certificate_sha256=certificate["sha256"],
                    )
                )
            except Exception as exc:  # OAK receipt instead of silent campaign loss.
                summary.failed += 1
                self.store.update_task(task, TaskState.FAILED, error=f"{type(exc).__name__}: {exc}")
                summary.receipts.append(
                    TaskReceipt(task.task_id, TaskState.FAILED, str(task.value), error=f"{type(exc).__name__}: {exc}")
                )
        summary.checkpoint = self.store.checkpoint(manifest.campaign_id)
        return summary
