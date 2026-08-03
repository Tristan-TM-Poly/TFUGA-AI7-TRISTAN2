from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping

from ..r03.canonical import sha256_hex
from ..r03.pocklington import verify_pocklington_certificate


@dataclass(frozen=True, slots=True)
class ProofNode:
    node_id: str
    n: int
    certificate: dict[str, Any]
    child_refs: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProofGraph:
    version: str
    root: str
    nodes: dict[str, ProofNode]
    oak: dict[str, Any]
    sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "root": self.root,
            "nodes": {key: node.to_dict() for key, node in sorted(self.nodes.items())},
            "oak": self.oak,
            "sha256": self.sha256,
        }


def _certificate_payload(certificate: Any) -> dict[str, Any]:
    if hasattr(certificate, "to_dict"):
        return copy.deepcopy(certificate.to_dict())
    return copy.deepcopy(dict(certificate))


def _strip_children(certificate: Mapping[str, Any]) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    stripped = copy.deepcopy(dict(certificate))
    children: dict[int, dict[str, Any]] = {}
    factors = []
    for raw_factor in stripped.get("factors", []):
        factor = dict(raw_factor)
        child = factor.get("child_certificate")
        prime = int(factor["prime"])
        if child is not None:
            children[prime] = copy.deepcopy(dict(child))
        factor["child_certificate"] = None
        factors.append(factor)
    stripped["factors"] = factors
    return stripped, children


def _node_id(certificate: Mapping[str, Any]) -> str:
    n = int(certificate["n"])
    digest = str(certificate.get("sha256") or sha256_hex(dict(certificate)))
    return f"pocklington-{n:x}-{digest[:16]}"


def seal_graph(payload: Mapping[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(dict(payload))
    sealed["sha256"] = ""
    sealed["sha256"] = sha256_hex(sealed)
    return sealed


def build_proof_graph(root_certificate: Any) -> ProofGraph:
    root_payload = _certificate_payload(root_certificate)
    nodes: dict[str, ProofNode] = {}
    seen_n: dict[int, str] = {}

    def visit(certificate: dict[str, Any]) -> str:
        node_id = _node_id(certificate)
        n = int(certificate["n"])
        existing = seen_n.get(n)
        if existing is not None and existing != node_id:
            raise ValueError(f"conflicting certificates for prime {n}")
        if node_id in nodes:
            return node_id
        stripped, children = _strip_children(certificate)
        refs: dict[str, str] = {}
        seen_n[n] = node_id
        nodes[node_id] = ProofNode(node_id, n, stripped, refs)
        for prime, child in sorted(children.items()):
            child_id = visit(child)
            refs[str(prime)] = child_id
        nodes[node_id] = ProofNode(node_id, n, stripped, refs)
        return node_id

    root = visit(root_payload)
    graph = ProofGraph(
        version="4.0",
        root=root,
        nodes=nodes,
        oak={
            "status": "RECURSIVE_POCKLINGTON_PROOF_DAG_R0_4",
            "deterministic_proof_claimed": True,
            "novelty_claimed": False,
            "record_claimed": False,
            "economic_value_claimed": False,
            "all_nodes_must_be_reachable": True,
        },
    )
    payload = graph.to_dict()
    payload["sha256"] = ""
    return replace(graph, sha256=sha256_hex(payload))


def _normalize_graph(graph: ProofGraph | Mapping[str, Any]) -> dict[str, Any]:
    return graph.to_dict() if isinstance(graph, ProofGraph) else copy.deepcopy(dict(graph))


def verify_proof_graph(graph: ProofGraph | Mapping[str, Any]) -> tuple[bool, list[str]]:
    payload = _normalize_graph(graph)
    errors: list[str] = []
    expected = str(payload.get("sha256", ""))
    unsigned = copy.deepcopy(payload)
    unsigned["sha256"] = ""
    if sha256_hex(unsigned) != expected:
        errors.append("proof graph sha256 mismatch")
    nodes = payload.get("nodes")
    root = payload.get("root")
    if not isinstance(nodes, dict) or not nodes:
        return False, errors + ["proof graph nodes missing"]
    if root not in nodes:
        return False, errors + ["proof graph root missing"]

    visiting: set[str] = set()
    visited: set[str] = set()
    reconstructed: dict[str, dict[str, Any]] = {}

    def rebuild(node_id: str) -> dict[str, Any] | None:
        if node_id in reconstructed:
            return reconstructed[node_id]
        if node_id in visiting:
            errors.append(f"cycle detected at {node_id}")
            return None
        raw_node = nodes.get(node_id)
        if not isinstance(raw_node, dict):
            errors.append(f"missing node {node_id}")
            return None
        if raw_node.get("node_id") != node_id:
            errors.append(f"node key/id mismatch for {node_id}")
        visiting.add(node_id)
        certificate = copy.deepcopy(raw_node.get("certificate", {}))
        try:
            n = int(raw_node["n"])
            if int(certificate["n"]) != n:
                errors.append(f"node/certificate n mismatch for {node_id}")
        except (KeyError, TypeError, ValueError):
            errors.append(f"malformed node {node_id}")
            visiting.remove(node_id)
            return None
        refs = raw_node.get("child_refs", {})
        if not isinstance(refs, dict):
            errors.append(f"child_refs malformed for {node_id}")
            refs = {}
        factor_primes: set[str] = set()
        rebuilt_factors = []
        for raw_factor in certificate.get("factors", []):
            factor = dict(raw_factor)
            prime_key = str(int(factor["prime"]))
            factor_primes.add(prime_key)
            child_id = refs.get(prime_key)
            if child_id is not None:
                child = rebuild(str(child_id))
                if child is None:
                    factor["child_certificate"] = None
                else:
                    if int(child.get("n", -1)) != int(prime_key):
                        errors.append(f"child prime mismatch for factor {prime_key}")
                    factor["child_certificate"] = child
            else:
                factor["child_certificate"] = None
            rebuilt_factors.append(factor)
        extra_refs = set(map(str, refs)) - factor_primes
        if extra_refs:
            errors.append(f"unused child refs for {node_id}: {sorted(extra_refs)}")
        certificate["factors"] = rebuilt_factors
        ok, certificate_errors = verify_pocklington_certificate(certificate)
        if not ok:
            errors.extend(f"{node_id}: {message}" for message in certificate_errors)
        visiting.remove(node_id)
        visited.add(node_id)
        reconstructed[node_id] = certificate
        return certificate

    rebuild(str(root))
    unreachable = set(nodes) - visited
    if unreachable:
        errors.append(f"unreachable proof nodes: {sorted(unreachable)}")
    oak = payload.get("oak", {})
    if oak.get("novelty_claimed") is not False or oak.get("record_claimed") is not False:
        errors.append("R0.4 proof graph may not claim novelty or a record")
    return not errors, errors
