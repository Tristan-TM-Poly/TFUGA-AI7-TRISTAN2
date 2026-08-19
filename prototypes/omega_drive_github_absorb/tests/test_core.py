from omega_drive_github_absorb.core import (
    DriveLinkResolver,
    HypergraphBuilder,
    ManifestBuilder,
    PermissionPolicy,
)


def test_resolves_drive_file_url():
    obj = DriveLinkResolver.resolve("https://drive.google.com/file/d/ABC_123/view?usp=sharing")
    assert obj.kind == "file"
    assert obj.drive_id == "ABC_123"


def test_resolves_drive_folder_url():
    obj = DriveLinkResolver.resolve("https://drive.google.com/drive/folders/FOLDER_123")
    assert obj.kind == "folder"
    assert obj.drive_id == "FOLDER_123"


def test_resolves_google_doc_url():
    obj = DriveLinkResolver.resolve("https://docs.google.com/document/d/DOC_123/edit")
    assert obj.kind == "doc"
    assert obj.drive_id == "DOC_123"


def test_unknown_link_is_high_risk():
    obj = DriveLinkResolver.resolve("https://example.com/not-drive")
    assert obj.kind == "unknown"
    assert obj.risk_level == "high"


def test_permission_gate_blocks_download_by_default():
    policy = PermissionPolicy(max_level="L3")
    assert policy.gate("L2") == "BLOCK_DOWNLOAD"


def test_permission_gate_allows_inventory_by_default():
    policy = PermissionPolicy()
    assert policy.gate("L1") == "ALLOW_INVENTORY_ONLY"


def test_manifest_and_seed_hypergraph():
    policy = PermissionPolicy()
    objects = [DriveLinkResolver.resolve("https://drive.google.com/file/d/ABC_123/view")]
    manifest = ManifestBuilder.build(objects, policy)
    assert manifest[0]["oak_status"] == "ALLOW_INVENTORY_ONLY"
    graph = HypergraphBuilder.from_manifest(manifest)
    assert graph["nodes"]
    assert graph["edges"]
