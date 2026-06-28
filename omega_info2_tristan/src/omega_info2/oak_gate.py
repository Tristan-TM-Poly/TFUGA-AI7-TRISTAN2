"""OAK information gate for Ω-INFO²-T."""

from __future__ import annotations

from .models import InfoObject, OAKReport, OAKStatus


class OAKInfoGate:
    """Evaluate whether an InfoObject is ready for action or canonization."""

    def __init__(self, min_truth: float = 0.60, min_source_trust: float = 0.45, max_risk: float = 0.70) -> None:
        self.min_truth = min_truth
        self.min_source_trust = min_source_trust
        self.max_risk = max_risk

    def evaluate(self, obj: InfoObject) -> OAKReport:
        passed: list[str] = []
        failed: list[str] = []
        residue: list[str] = []

        def check(name: str, condition: bool, residue_text: str | None = None) -> None:
            if condition:
                passed.append(name)
            else:
                failed.append(name)
                if residue_text:
                    residue.append(residue_text)

        check("source_known", bool(obj.meta.source), "Source missing or underspecified.")
        check("date_or_version_known", bool(obj.meta.date_created or obj.meta.version != "unknown"), "Date/version unknown.")
        check("provenance_present", bool(obj.provenance.transformations), "No transformation chain recorded.")
        check("uncertainty_estimated", obj.uncertainty.mean < 0.85, "Uncertainty tensor too high or defaulted.")
        check("claims_present", bool(obj.claims or obj.concepts or obj.equations), "No extracted claims/concepts/equations.")
        check("risk_bounded", obj.scores.risk <= self.max_risk, "Risk exceeds OAK threshold.")
        check("source_trust_minimum", obj.scores.source_trust >= self.min_source_trust, "Source trust below threshold.")
        check("truth_not_overclaimed", obj.scores.truth >= self.min_truth or obj.scores.testability >= 0.70, "Truth is low and no strong test path exists.")
        check("proof_separated_from_fertility", obj.scores.truth != obj.scores.fertility, "Truth and fertility appear collapsed into one score.")

        if obj.scores.ip_sensitivity >= 0.70:
            status = OAKStatus.IP_SENSITIVE
            residue.append("Potential IP sensitivity: protect before public release.")
        elif obj.scores.risk >= 0.85:
            status = OAKStatus.DANGEROUS
            residue.append("High risk: human review required.")
        elif failed:
            status = OAKStatus.TESTABLE if obj.scores.testability >= 0.70 else OAKStatus.PARSED
        elif obj.scores.truth >= 0.85 and obj.scores.source_trust >= 0.75 and obj.scores.risk <= 0.25:
            status = OAKStatus.ROBUST
        else:
            status = OAKStatus.TESTED if obj.scores.testability >= 0.60 else OAKStatus.LINKED

        next_test = self._recommend_next_test(obj, failed)
        report = OAKReport(status=status, checks_passed=passed, checks_failed=failed, residue=residue, next_test=next_test)
        obj.oak = report
        return report

    @staticmethod
    def _recommend_next_test(obj: InfoObject, failed: list[str]) -> str | None:
        if "source_known" in failed:
            return "Find primary source or record explicit provenance."
        if "provenance_present" in failed:
            return "Record transformation chain from raw object to extracted claims."
        if obj.scores.testability >= 0.70:
            return "Run benchmark/test linked to the strongest extracted claim."
        if obj.scores.ip_sensitivity >= 0.70:
            return "Classify IP before publication or external sharing."
        if obj.scores.risk >= 0.70:
            return "Perform OAK risk review and add M⁻ prevention rules."
        return "Link to Info2Graph and search for counter-evidence."
