from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .api_layer import (
    GitHubSearchIntent,
    compile_github_code_query,
    compile_github_repository_query,
    compile_stackoverflow_query,
    digest_github_search,
    local_dependency_inventory,
    scan_text_for_secrets,
)
from .license_gate import batch_classify
from .oak_runner import oak_decision
from .report import load_source, markdown_report
from .scorer import DigestScore


def _github_intent_from_args(args: argparse.Namespace) -> GitHubSearchIntent:
    return GitHubSearchIntent(
        keywords=tuple(args.keywords),
        language=args.language,
        license=args.license_id,
        min_stars=args.min_stars,
        pushed_after=args.pushed_after,
        topic=args.topic,
        user=args.user,
        org=args.org,
        filename=getattr(args, "filename", None),
        path=getattr(args, "path", None),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="oss-digest", description="Ω-OSS-DIGEST-T CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_license = sub.add_parser("license", help="Classify SPDX/license identifiers")
    p_license.add_argument("licenses", nargs="+")

    p_score = sub.add_parser("score", help="Compute OAK digest score")
    for name in ["fit", "license", "tests", "security", "maintainability", "cvcd", "utility", "activity", "risk"]:
        p_score.add_argument(f"--{name}", type=float, default=None)

    p_report = sub.add_parser("report", help="Generate Markdown OAK report from JSON/YAML source record")
    p_report.add_argument("source_file")
    p_report.add_argument("--out", default=None)

    p_compile = sub.add_parser("compile-github", help="Compile a GitHub repository search query")
    p_compile.add_argument("keywords", nargs="+")
    p_compile.add_argument("--language")
    p_compile.add_argument("--license-id")
    p_compile.add_argument("--min-stars", type=int)
    p_compile.add_argument("--pushed-after")
    p_compile.add_argument("--topic")
    p_compile.add_argument("--user")
    p_compile.add_argument("--org")

    p_code = sub.add_parser("compile-code", help="Compile a GitHub code search query")
    p_code.add_argument("keywords", nargs="+")
    p_code.add_argument("--language")
    p_code.add_argument("--filename")
    p_code.add_argument("--path")
    p_code.add_argument("--user")
    p_code.add_argument("--org")
    p_code.set_defaults(license_id=None, min_stars=None, pushed_after=None, topic=None)

    p_gh = sub.add_parser("github-search", help="Search GitHub repositories and emit OAK source records")
    p_gh.add_argument("keywords", nargs="+")
    p_gh.add_argument("--language")
    p_gh.add_argument("--license-id")
    p_gh.add_argument("--min-stars", type=int)
    p_gh.add_argument("--pushed-after")
    p_gh.add_argument("--topic")
    p_gh.add_argument("--user")
    p_gh.add_argument("--org")
    p_gh.add_argument("--limit", type=int, default=5)

    p_stack_compile = sub.add_parser("compile-stack", help="Compile StackOverflow query parameters")
    p_stack_compile.add_argument("keywords", nargs="+")
    p_stack_compile.add_argument("--tag", action="append", default=[])

    p_scan = sub.add_parser("scan-local", help="Run local secret/dependency scan")
    p_scan.add_argument("root")

    args = parser.parse_args(argv)

    if args.cmd == "license":
        print(json.dumps([asdict(x) for x in batch_classify(args.licenses)], ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "score":
        score = DigestScore(
            fit=args.fit if args.fit is not None else 0.5,
            license_compatibility=args.license if args.license is not None else 0.5,
            tests=args.tests if args.tests is not None else 0.5,
            security=args.security if args.security is not None else 0.5,
            maintainability=args.maintainability if args.maintainability is not None else 0.5,
            cvcd_compressibility=args.cvcd if args.cvcd is not None else 0.5,
            utility=args.utility if args.utility is not None else 0.5,
            community_activity=args.activity if args.activity is not None else 0.5,
            risk=args.risk if args.risk is not None else 0.2,
        )
        print(json.dumps(asdict(oak_decision("MIT", score)), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "report":
        source = load_source(args.source_file)
        md = markdown_report(source)
        if args.out:
            Path(args.out).write_text(md, encoding="utf-8")
        else:
            print(md)
        return 0

    if args.cmd == "compile-github":
        print(compile_github_repository_query(_github_intent_from_args(args)))
        return 0

    if args.cmd == "compile-code":
        print(compile_github_code_query(_github_intent_from_args(args)))
        return 0

    if args.cmd == "github-search":
        print(json.dumps(digest_github_search(_github_intent_from_args(args), limit=args.limit), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "compile-stack":
        print(json.dumps(compile_stackoverflow_query(tuple(args.keywords), tuple(args.tag)), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "scan-local":
        root = Path(args.root)
        findings = []
        for suffix in ["*.py", "*.js", "*.ts", "*.json", "*.yaml", "*.yml", "*.toml", ".env"]:
            for file in root.rglob(suffix):
                if file.is_file():
                    for finding in scan_text_for_secrets(file.read_text(encoding="utf-8", errors="ignore")):
                        findings.append({"file": str(file), **asdict(finding)})
        print(json.dumps({"root": str(root), "secret_findings": findings, "dependency_inventory": local_dependency_inventory(root), "oak_status": "OAK_RED_SECURITY" if findings else "OAK_GREEN_LOCAL_SCAN"}, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
