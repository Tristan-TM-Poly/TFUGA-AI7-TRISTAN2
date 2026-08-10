from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import re
import time

SCHEMA_VERSION = "0.1.0"
EXTRACTOR_VERSION = "0.1.0"

SECRET_PATTERNS = (
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"(?i)\b(api[_ -]?key|password|passwd|secret|token)\s*[:=]\s*[^\s,;]{8,}"),
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
OMEGA_RE = re.compile(r"Ω[\w\-‑–—²³⁴⁵⁶⁷⁸⁹⁰∞+]+", re.UNICODE)
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9][A-Z0-9²³⁴⁵⁶⁷⁸⁹⁰+_-]{1,}\b")
GO_RE = re.compile(r"(?im)^\s*(GO(?:\s+@[A-Za-z0-9_-]+)?(?:\s+[A-Z0-9²∞_@+-]+)*)\s*$")
MATH_BLOCK_RE = re.compile(r"\\\[(.*?)\\\]|\$\$(.*?)\$\$", re.S)
DECISION_CUES = (
    "je veux", "il faut", "priorité", "prioritaire", "on va", "nous allons",
    "next action", "prochaine action", "décision", "decision", "doit être",
    "doit etre", "should ", "must ",
)
IP_CUES = ("brevet", "patent", "secret commercial", "trade secret", "confidentiel", "confidential")
HYPOTHESIS_CUES = ("je pense", "i think", "hypothèse", "hypothesis", "conjecture", "propose", "proposer")
DEFINITION_CUES = ("défin", "define", "appelons", "nommons", "canonical", "canonique")
MEASURE_CUES = ("mesuré", "measured", "benchmark", "résultat expérimental", "experimental result")
PROOF_CUES = ("preuve formelle", "formal proof", "qed", "theorem proved")


@dataclass(frozen=True)
class PipelineResult:
    output_dir: str
    manifest_path: str
    node_count: int
    hyperedge_count: int
    provenance_count: int
    secret_redactions: int


def _json_dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def stable_id(prefix: str, *parts: Any) -> str:
    payload = "\x1f".join(_json_dump(p) if not isinstance(p, str) else p for p in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{digest}"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def redact_secrets(text: str) -> tuple[str, int]:
    count = 0
    out = text
    for pattern in SECRET_PATTERNS:
        out, n = pattern.subn("[REDACTED_SECRET]", out)
        count += n
    return out, count


def classify_sensitivity(original_text: str) -> str:
    if any(p.search(original_text) for p in SECRET_PATTERNS):
        return "SECRET"
    low = original_text.lower()
    if any(cue in low for cue in IP_CUES):
        return "IP_SENSITIVE"
    if EMAIL_RE.search(original_text):
        return "PERSONAL"
    return "PUBLIC"


def epistemic_state(text: str, role: str) -> str:
    low = text.lower()
    if any(c in low for c in PROOF_CUES):
        # Automatic extraction cannot independently certify a proof.
        return "SUPPORTED"
    if any(c in low for c in MEASURE_CUES):
        return "MEASURED_RESULT"
    if any(c in low for c in DEFINITION_CUES):
        return "DEFINITION"
    if any(c in low for c in HYPOTHESIS_CUES):
        return "USER_PROPOSAL" if role == "user" else "HYPOTHESIS"
    return "USER_PROPOSAL" if role == "user" else "MODEL"


def importance_components(kind: str, text: str, relations: int = 0) -> dict[str, float]:
    low = text.lower()
    durability = 0.75 if kind in {"Concept", "Theory", "System", "Definition"} else 0.45
    reuse = min(1.0, 0.35 + 0.08 * relations + (0.25 if "omega" in low or "Ω" in text else 0.0))
    centrality = min(1.0, 0.3 + 0.07 * relations)
    evidence = 0.65 if any(x in low for x in ("test", "benchmark", "preuve", "evidence", "mesur")) else 0.3
    actionability = 0.75 if kind in {"Decision", "NextAction", "Command"} else 0.35
    novelty = 0.55
    project_dependency = 0.75 if kind in {"System", "Decision", "NextAction"} else 0.4
    historical_value = 0.7 if kind in {"Conversation", "Decision", "System"} else 0.45
    uncertainty = 0.7 if any(c in low for c in HYPOTHESIS_CUES) else 0.3
    duplication = 0.0
    sensitivity = 0.0
    score = (
        0.14 * durability + 0.14 * reuse + 0.12 * centrality + 0.12 * evidence
        + 0.12 * actionability + 0.08 * novelty + 0.12 * project_dependency
        + 0.08 * historical_value - 0.05 * uncertainty - 0.03 * duplication
        - 0.02 * sensitivity
    )
    return {
        "durability": round(durability, 4),
        "reuse": round(reuse, 4),
        "centrality": round(centrality, 4),
        "evidence": round(evidence, 4),
        "actionability": round(actionability, 4),
        "novelty": round(novelty, 4),
        "project_dependency": round(project_dependency, 4),
        "historical_value": round(historical_value, 4),
        "uncertainty": round(uncertainty, 4),
        "duplication": round(duplication, 4),
        "sensitivity": round(sensitivity, 4),
        "score": round(max(0.0, min(1.0, score)), 4),
    }


def _content_to_text(content: Any) -> str:
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        parts = content.get("parts")
        if isinstance(parts, list):
            out = []
            for part in parts:
                if isinstance(part, str):
                    out.append(part)
                elif part is not None:
                    out.append(json.dumps(part, ensure_ascii=False, sort_keys=True))
            return "\n".join(out)
        if "text" in content and isinstance(content["text"], str):
            return content["text"]
    if isinstance(content, list):
        return "\n".join(_content_to_text(x) for x in content)
    return str(content)


def _iter_official_mapping(conv: dict[str, Any]) -> Iterable[dict[str, Any]]:
    mapping = conv.get("mapping")
    if not isinstance(mapping, dict):
        return []
    records = []
    for node_id, node in mapping.items():
        if not isinstance(node, dict):
            continue
        msg = node.get("message")
        if not isinstance(msg, dict):
            continue
        author = msg.get("author") or {}
        role = author.get("role") if isinstance(author, dict) else "unknown"
        content = _content_to_text(msg.get("content"))
        if not content.strip():
            continue
        records.append(
            {
                "message_id": str(msg.get("id") or node_id),
                "node_id": str(node_id),
                "role": str(role or "unknown"),
                "create_time": msg.get("create_time") or node.get("create_time"),
                "content": content,
            }
        )
    records.sort(key=lambda x: (x["create_time"] is None, x["create_time"] or 0, x["message_id"]))
    return records


def load_conversations(path: str | Path) -> list[dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict) and isinstance(raw.get("conversations"), list):
        convs = raw["conversations"]
    elif isinstance(raw, list):
        convs = raw
    elif isinstance(raw, dict):
        convs = [raw]
    else:
        raise ValueError("Unsupported ChatGPT export shape")

    normalized = []
    for idx, conv in enumerate(convs):
        if not isinstance(conv, dict):
            continue
        conv_id = str(conv.get("id") or conv.get("conversation_id") or stable_id("conversation", idx, conv.get("title", "")))
        title = str(conv.get("title") or f"Conversation {idx + 1}")
        messages = list(_iter_official_mapping(conv))
        if not messages and isinstance(conv.get("messages"), list):
            for j, msg in enumerate(conv["messages"]):
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role") or ((msg.get("author") or {}).get("role") if isinstance(msg.get("author"), dict) else "unknown")
                text = _content_to_text(msg.get("content") or msg.get("text"))
                if text.strip():
                    messages.append({
                        "message_id": str(msg.get("id") or stable_id("message", conv_id, j)),
                        "node_id": str(msg.get("id") or j),
                        "role": str(role or "unknown"),
                        "create_time": msg.get("create_time") or msg.get("timestamp"),
                        "content": text,
                    })
        normalized.append({
            "id": conv_id,
            "title": title,
            "create_time": conv.get("create_time"),
            "update_time": conv.get("update_time"),
            "messages": messages,
        })
    return normalized


def _make_node(kind: str, label: str, text: str, source_ref: dict[str, Any] | None = None, role: str = "system") -> dict[str, Any]:
    norm = normalize_text(text)
    node_id = stable_id(kind.lower(), kind, norm.lower())
    imp = importance_components(kind, norm)
    sensitivity = classify_sensitivity(text)
    imp["sensitivity"] = 1.0 if sensitivity in {"SECRET", "IP_SENSITIVE"} else (0.5 if sensitivity == "PERSONAL" else 0.0)
    imp["score"] = round(max(0.0, imp["score"] - 0.02 * imp["sensitivity"]), 4)
    node = {
        "id": node_id,
        "kind": kind,
        "label": label[:160],
        "text": norm,
        "epistemic_state": epistemic_state(norm, role),
        "importance": imp,
        "sensitivity": sensitivity,
        "status": "ACTIVE",
        "schema_version": SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
    }
    if source_ref:
        node["source_ref"] = source_ref
    return node


def _relation(edge_type: str, members: list[str], source_ref: dict[str, Any] | None = None) -> dict[str, Any]:
    edge = {
        "id": stable_id("edge", edge_type, sorted(members)),
        "type": edge_type,
        "members": members,
        "schema_version": SCHEMA_VERSION,
    }
    if source_ref:
        edge["source_ref"] = source_ref
    return edge


def _extract_atomic_nodes(text: str, source_ref: dict[str, Any], role: str) -> list[tuple[dict[str, Any], str]]:
    out: list[tuple[dict[str, Any], str]] = []
    seen: set[str] = set()

    for match in list(OMEGA_RE.finditer(text)) + list(ACRONYM_RE.finditer(text)):
        token = match.group(0).strip(".,;:()[]{}")
        if len(token) < 3 or token in seen or "REDACTED" in token or token == "SECRET":
            continue
        seen.add(token)
        kind = "System" if token.startswith("Ω") else "Concept"
        out.append((_make_node(kind, token, token, source_ref, role), "mentions"))

    for match in GO_RE.finditer(text):
        cmd = normalize_text(match.group(1))
        if cmd and cmd not in seen:
            seen.add(cmd)
            out.append((_make_node("Command", cmd, cmd, source_ref, role), "requests_action"))

    for match in MATH_BLOCK_RE.finditer(text):
        expr = normalize_text(match.group(1) or match.group(2) or "")
        if len(expr) >= 3 and expr not in seen:
            seen.add(expr)
            out.append((_make_node("Equation", expr[:80], expr, source_ref, role), "states"))

    for line in text.splitlines():
        nline = normalize_text(line)
        if not nline or len(nline) < 8 or "[REDACTED_SECRET]" in nline:
            continue
        low = nline.lower()
        if any(cue in low for cue in DECISION_CUES):
            key = "decision:" + nline.lower()
            if key not in seen:
                seen.add(key)
                kind = "NextAction" if ("next action" in low or "prochaine action" in low or low.startswith("go ")) else "Decision"
                out.append((_make_node(kind, nline[:100], nline, source_ref, role), "states"))
    return out


def build_graph(conversations: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
    nodes_by_id: dict[str, dict[str, Any]] = {}
    edges_by_id: dict[str, dict[str, Any]] = {}
    provenance: list[dict[str, Any]] = []
    redactions = 0

    for conv in conversations:
        conv_source = {"conversation_id": conv["id"], "source_type": "chatgpt_export"}
        conv_node = _make_node("Conversation", conv["title"], conv["title"], conv_source, "system")
        conv_node["id"] = stable_id("conversation", conv["id"])
        conv_node["conversation_id"] = conv["id"]
        conv_node["create_time"] = conv.get("create_time")
        conv_node["update_time"] = conv.get("update_time")
        nodes_by_id[conv_node["id"]] = conv_node

        for msg in conv["messages"]:
            original = msg["content"]
            safe_text, nredact = redact_secrets(original)
            redactions += nredact
            source_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
            source_ref = {
                "source_type": "chatgpt_export",
                "conversation_id": conv["id"],
                "message_id": msg["message_id"],
                "timestamp": msg.get("create_time"),
                "role": msg["role"],
                "source_hash": source_hash,
            }
            msg_node = _make_node("Message", f"{msg['role']} message", safe_text, source_ref, msg["role"])
            msg_node["id"] = stable_id("message", conv["id"], msg["message_id"], source_hash)
            msg_node["role"] = msg["role"]
            nodes_by_id[msg_node["id"]] = msg_node

            contains = _relation("contains", [conv_node["id"], msg_node["id"]], source_ref)
            edges_by_id[contains["id"]] = contains
            provenance.append({
                "derived_id": msg_node["id"],
                **source_ref,
                "extractor_version": EXTRACTOR_VERSION,
                "source_span": "full_message",
            })

            for atom_node, rel_type in _extract_atomic_nodes(safe_text, source_ref, msg["role"]):
                existing = nodes_by_id.get(atom_node["id"])
                if existing:
                    existing.setdefault("occurrences", 1)
                    existing["occurrences"] += 1
                    existing.setdefault("source_refs", []).append(source_ref)
                else:
                    atom_node["occurrences"] = 1
                    nodes_by_id[atom_node["id"]] = atom_node
                edge = _relation(rel_type, [msg_node["id"], atom_node["id"]], source_ref)
                edges_by_id[edge["id"]] = edge
                provenance.append({
                    "derived_id": atom_node["id"],
                    **source_ref,
                    "extractor_version": EXTRACTOR_VERSION,
                    "source_span": "heuristic_extraction",
                })

    return list(nodes_by_id.values()), list(edges_by_id.values()), provenance, redactions


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _oak_report(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], provenance: list[dict[str, Any]], redactions: int) -> dict[str, Any]:
    node_ids = {n["id"] for n in nodes}
    bad_edges = [e["id"] for e in edges if any(m not in node_ids for m in e.get("members", []))]
    derived = {p["derived_id"] for p in provenance}
    source_required = [n["id"] for n in nodes if n["kind"] != "Conversation"]
    missing_provenance = [nid for nid in source_required if nid not in derived]
    secret_leaks = []
    for n in nodes:
        if any(p.search(n.get("text", "")) for p in SECRET_PATTERNS):
            secret_leaks.append(n["id"])
    status = "PASS" if not bad_edges and not secret_leaks else "FAIL"
    return {
        "status": status,
        "schema_version": SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "node_count": len(nodes),
        "hyperedge_count": len(edges),
        "provenance_count": len(provenance),
        "dangling_hyperedges": bad_edges,
        "missing_provenance": missing_provenance,
        "secret_redactions": redactions,
        "secret_leaks": secret_leaks,
        "gate": "PROMOTE" if status == "PASS" else "REJECT",
        "notes": [
            "PROMOTE certifies structural/provenance/privacy checks only; it does not certify scientific truth.",
            "Automatic epistemic classification never upgrades extracted proof language to PROVEN.",
        ],
    }


def _memory_candidates(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    allowed = {"System", "Concept", "Decision", "NextAction", "Command"}
    for node in nodes:
        if node["kind"] not in allowed:
            continue
        score = float(node.get("importance", {}).get("score", 0.0))
        if score < 0.52:
            continue
        sensitivity = node.get("sensitivity", "PUBLIC")
        action = "REVIEW"
        if sensitivity != "PUBLIC":
            action = "DO_NOT_SAVE"
        elif node["kind"] in {"NextAction", "Command"}:
            action = "EXTERNAL_ONLY"
        candidates.append({
            "id": stable_id("memorycandidate", node["id"]),
            "statement": node.get("text", ""),
            "reason": f"{node['kind']} with importance={score:.4f}",
            "durability_score": node["importance"].get("durability"),
            "reuse_score": node["importance"].get("reuse"),
            "importance_score": score,
            "sensitivity": sensitivity,
            "source_node": node["id"],
            "epistemic_state": node.get("epistemic_state"),
            "recommended_action": action,
        })
    candidates.sort(key=lambda x: (-x["importance_score"], x["statement"]))
    return candidates


def _capsule(nodes: list[dict[str, Any]], title: str) -> str:
    selected = [
        n for n in nodes
        if n["kind"] not in {"Message", "Conversation"}
        and n.get("sensitivity") == "PUBLIC"
    ]
    selected.sort(key=lambda n: (-float(n["importance"]["score"]), n["kind"], n["label"]))
    systems = [n for n in selected if n["kind"] == "System"][:24]
    actions = [n for n in selected if n["kind"] in {"Decision", "NextAction", "Command"}][:16]
    concepts = [n for n in selected if n["kind"] == "Concept"][:24]

    lines = [
        f"# {title}",
        "",
        "> Generated from the HGFM graph. This is a compact retrieval artifact, not a source of truth.",
        "",
        "## Core systems",
    ]
    lines += [f"- `{n['label']}` — OAK state `{n['epistemic_state']}`; importance {n['importance']['score']}" for n in systems] or ["- None extracted yet."]
    lines += ["", "## Important concepts"]
    lines += [f"- `{n['label']}`" for n in concepts] or ["- None extracted yet."]
    lines += ["", "## Decisions / actions"]
    lines += [f"- {n['text']}" for n in actions] or ["- None extracted yet."]
    lines += [
        "",
        "## Retrieval rule",
        "Load the smallest relevant subgraph for the current task; consult M− before regenerating previously rejected ideas.",
        "",
        "## Epistemic rule",
        "Conversation ≠ memory ≠ truth. Repetition is not evidence; provenance and OAK state must remain attached.",
        "",
    ]
    return "\n".join(lines)


def _context_doc(nodes: list[dict[str, Any]], oak: dict[str, Any]) -> str:
    selected = [
        n for n in nodes
        if n["kind"] in {"System", "Concept", "Decision", "NextAction", "Command"}
        and n.get("sensitivity") == "PUBLIC"
    ]
    selected.sort(key=lambda n: (-float(n["importance"]["score"]), n["label"]))
    lines = [
        "# CHATGPT_CONTEXT",
        "",
        f"OAK structural gate: **{oak['status']}**. Nodes: {oak['node_count']}; hyperedges: {oak['hyperedge_count']}.",
        "",
        "This document is generated. Prefer graph retrieval over loading the complete corpus.",
        "",
        "## High-signal memory",
    ]
    lines += [f"- [{n['kind']}] {n['text']}" for n in selected[:80]] or ["- No extracted public memory yet."]
    lines += ["", "## Guardrails", "- Keep provenance.", "- Keep M+ and M− separate.", "- Never treat a hypothesis as proof.", "- Never expose raw private transcripts in a public repository.", ""]
    return "\n".join(lines)


def run_pipeline(input_path: str | Path, output_dir: str | Path) -> PipelineResult:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    conversations = load_conversations(input_path)
    nodes, edges, provenance, redactions = build_graph(conversations)

    _write_jsonl(output / "hgfm" / "nodes.jsonl", nodes)
    _write_jsonl(output / "hgfm" / "hyperedges.jsonl", edges)
    _write_jsonl(output / "hgfm" / "provenance.jsonl", provenance)

    concepts = [n for n in nodes if n["kind"] in {"Concept", "System"}]
    (output / "indexes").mkdir(parents=True, exist_ok=True)
    (output / "indexes" / "concepts.json").write_text(json.dumps(concepts, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (output / "indexes" / "conversations.json").write_text(
        json.dumps([{"id": c["id"], "title": c["title"], "message_count": len(c["messages"])} for c in conversations], ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    candidates = _memory_candidates(nodes)
    _write_jsonl(output / "candidates" / "memory_candidates.jsonl", candidates)

    oak = _oak_report(nodes, edges, provenance, redactions)
    (output / "reports").mkdir(parents=True, exist_ok=True)
    (output / "reports" / "oak_report.json").write_text(json.dumps(oak, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    (output / "canon").mkdir(parents=True, exist_ok=True)
    (output / "canon" / "MEMORY_CAPSULE.md").write_text(_capsule(nodes, "MEMORY_CAPSULE"), encoding="utf-8")
    (output / "canon" / "CHATGPT_CONTEXT.md").write_text(_context_doc(nodes, oak), encoding="utf-8")
    (output / "canon" / "MASTER_MEMORY_INDEX.md").write_text(
        "# MASTER_MEMORY_INDEX\n\n"
        f"- Conversations: {len(conversations)}\n"
        f"- Nodes: {len(nodes)}\n"
        f"- Hyperedges: {len(edges)}\n"
        f"- Provenance records: {len(provenance)}\n"
        f"- OAK: {oak['status']}\n"
        f"- Secret redactions: {redactions}\n",
        encoding="utf-8",
    )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "generated_at_unix": int(time.time()),
        "input_sha256": hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),
        "conversation_count": len(conversations),
        "node_count": len(nodes),
        "hyperedge_count": len(edges),
        "provenance_count": len(provenance),
        "secret_redactions": redactions,
        "oak_status": oak["status"],
        "raw_transcripts_committed": False,
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    return PipelineResult(
        output_dir=str(output),
        manifest_path=str(manifest_path),
        node_count=len(nodes),
        hyperedge_count=len(edges),
        provenance_count=len(provenance),
        secret_redactions=redactions,
    )


def recall(output_dir: str | Path, query: str, limit: int = 24) -> dict[str, Any]:
    output = Path(output_dir)
    nodes = _read_jsonl(output / "hgfm" / "nodes.jsonl")
    edges = _read_jsonl(output / "hgfm" / "hyperedges.jsonl")
    q = normalize_text(query).lower()
    tokens = [t for t in re.split(r"\W+", q) if t]

    def score(node: dict[str, Any]) -> float:
        hay = (node.get("label", "") + " " + node.get("text", "")).lower()
        exact = 3.0 if q and q in hay else 0.0
        token_score = sum(1.0 for t in tokens if t in hay)
        imp = float(node.get("importance", {}).get("score", 0.0))
        return exact + token_score + imp

    ranked = [(score(n), n) for n in nodes]
    ranked = [(s, n) for s, n in ranked if s > float(n.get("importance", {}).get("score", 0.0))]
    ranked.sort(key=lambda x: (-x[0], x[1]["id"]))
    selected = [n for _, n in ranked[:limit]]
    selected_ids = {n["id"] for n in selected}
    related = [e for e in edges if any(m in selected_ids for m in e.get("members", []))]
    neighbor_ids = {m for e in related for m in e.get("members", [])}
    neighbors = [n for n in nodes if n["id"] in neighbor_ids and n["id"] not in selected_ids]
    return {"query": query, "matches": selected, "neighbors": neighbors[:limit], "hyperedges": related[: limit * 3]}


def diff_manifests(old_manifest: str | Path, new_manifest: str | Path) -> dict[str, Any]:
    old = json.loads(Path(old_manifest).read_text(encoding="utf-8"))
    new = json.loads(Path(new_manifest).read_text(encoding="utf-8"))
    keys = ("conversation_count", "node_count", "hyperedge_count", "provenance_count", "secret_redactions")
    return {
        "old_sha256": old.get("input_sha256"),
        "new_sha256": new.get("input_sha256"),
        "changed": old.get("input_sha256") != new.get("input_sha256"),
        "deltas": {k: int(new.get(k, 0)) - int(old.get(k, 0)) for k in keys},
        "old_oak": old.get("oak_status"),
        "new_oak": new.get("oak_status"),
    }
