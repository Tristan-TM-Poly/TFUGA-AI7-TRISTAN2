from pathlib import Path

from omega_intercompany_mesh_t.generator import default_nodes, generate_mesh, write_mesh
from omega_intercompany_mesh_t.models import AgreementFamily, PacketStatus


def test_default_topology():
    nodes = default_nodes()
    assert len(nodes) == 4
    assert sum(node.company_id == "tristan_parent" for node in nodes) == 1


def test_complete_directed_mesh():
    agreements, messages = generate_mesh()
    assert len(agreements) == 4 * 3 * len(AgreementFamily) == 84
    assert len(messages) == 4 * 3 * 2 == 24
    assert len({(m.source_company_id, m.destination_company_id) for m in messages if m.stage == "BOOTSTRAP_REQUEST"}) == 12


def test_all_packets_non_binding_and_hashed():
    agreements, _ = generate_mesh()
    assert all(item.status is PacketStatus.DRAFT_NON_BINDING for item in agreements)
    assert all(item.content_hash and len(item.content_hash) == 64 for item in agreements)
    assert all(item.human_approval_required for item in agreements)


def test_mail_cannot_external_send():
    _, messages = generate_mesh()
    assert all(not item.external_send_allowed for item in messages)
    assert sum(item.auto_reply for item in messages) == 12


def test_write_manifest(tmp_path: Path):
    manifest = write_mesh(tmp_path)
    assert manifest == {
        "nodes": 4,
        "directed_relationships": 12,
        "agreement_families": 7,
        "agreement_packets": 84,
        "mail_packets": 24,
        "real_external_sends": 0,
    }
    assert (tmp_path / "agreements.jsonl").exists()
