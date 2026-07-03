from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from .license_gate import classify_license
from .oak_runner import oak_decision
from .scorer import DigestScore


def load_source(path: str | Path) -> dict:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"} and yaml:
        return yaml.safe_load(text)
    if p.suffix.lower() in {".yaml", ".yml"} and not yaml:
        data = {}
        for line in text.splitlines():
            if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
        return data
    return json.loads(text)


def markdown_report(source: dict) -> str:
    license_id = source.get("license_id") or source.get("license")
    score = DigestScore(
        fit=float(source.get("fit", 0.7)),
        license_compatibility=float(source.get("license_compatibility", 0.7)),
        tests=float(source.get("tests", 0.5)),
        security=float(source.get("security", 0.5)),
        maintainability=float(source.get("maintainability", 0.5)),
        cvcd_compressibility=float(source.get("cvcd_compressibility", 0.6)),
        utility=float(source.get("utility", 0.7)),
        community_activity=float(source.get("community_activity", 0.5)),
        risk=float(source.get("risk", 0.3)),
    )
    ldec = classify_license(license_id)
    odec = oak_decision(license_id, score)
    name = source.get("name", source.get("source_id", "unknown-source"))
    url = source.get("url", "")
    lines = [
        f"# Ω-OSS-DIGEST Report — {name}",
        "",
        f"- Source: `{source.get('source_id', name)}`",
        f"- URL: {url}",
        f"- License: `{ldec.license_id}` / `{ldec.license_class.value}`",
        f"- License OAK: `{ldec.oak_status}`",
        f"- Digest score: `{odec.score}`",
        f"- Final status: `{odec.status}`",
        "",
        "## Required actions",
    ]
    lines += [f"- {action}" for action in odec.required_actions]
    lines += ["", "## License notes"]
    lines += [f"- {note}" for note in ldec.notes]
    lines += ["", "## Raw score vector", "", "```json", json.dumps(asdict(score.normalized()), indent=2), "```"]
    return "\n".join(lines) + "\n"
