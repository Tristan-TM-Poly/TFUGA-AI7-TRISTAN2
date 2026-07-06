"""CI report helper."""


def ci_gate(job_ok: bool, report_code: int | None = None) -> str:
    if not job_ok:
        return "blocked"
    if report_code not in (None, 0):
        return "review"
    return "ok"
