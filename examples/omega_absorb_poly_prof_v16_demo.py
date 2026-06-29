from pathlib import Path
import json

from omega_prof_poly_t import run_cli


def main() -> None:
    path = Path("generated/omega_absorb_poly_prof_v16_demo_records.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([{"id": "demo", "title": "Demo record", "authors": ["A"]}]), encoding="utf-8")
    print(run_cli(["version"]).strip())
    print(run_cli(["route-source", "--input", str(path)]).strip())
    print(run_cli(["policy-check", "--input", str(path)]).strip())
    print(run_cli(["ingest-json-v2", "--input", str(path)]).strip())
    print(run_cli(["write-actions", "--source", "combined"]).strip())
    print(run_cli(["github-bundle", "--source", "combined"]).strip())


if __name__ == "__main__":
    main()
