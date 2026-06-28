from pathlib import Path

from omega_prof_poly_t import (
    build_export_bundle,
    build_package_health_report,
    generate_changelog,
    run_cli,
)


def main() -> None:
    out = Path("generated/omega_absorb_poly_prof_v13_demo")
    bundle = build_export_bundle("combined", out)
    print(run_cli(["version"]).strip())
    print("table_header", run_cli(["table", "--source", "combined"]).splitlines()[0])
    print("health", build_package_health_report().score)
    print("bundle_files", len(bundle.files))
    print("changelog", generate_changelog().splitlines()[0])


if __name__ == "__main__":
    main()
