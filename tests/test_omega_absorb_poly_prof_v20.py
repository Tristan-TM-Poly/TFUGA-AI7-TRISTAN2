from omega_prof_poly_t import (
    VERSION,
    build_cli_command_groups,
    build_omega_absorb_os_v2,
    build_package_layout_v2,
    build_report_bundle_contract,
    build_workflow_seed,
    render_cli_command_groups,
    render_omega_absorb_os_v2,
    render_package_layout_v2,
    render_report_bundle_contract,
    render_workflow_seed,
    run_cli,
)


def test_v20_cli_commands():
    assert VERSION == "2.0.0"
    assert run_cli(["version"]) == "omega-absorb 2.0.0\n"
    assert run_cli(["layout-v2"]).startswith("# Omega Absorb Package Layout v2")
    assert run_cli(["report-contract"]).startswith("# Report Bundle Contract")
    assert run_cli(["workflow-seed"]).startswith("# Workflow Seed")
    assert run_cli(["command-groups"]).startswith("# Omega Absorb CLI Command Groups")
    assert run_cli(["absorb-os"]).startswith("# Omega Absorb OS v2")


def test_layout_and_contract():
    layout = build_package_layout_v2()
    assert len(layout.sections) >= 10
    assert render_package_layout_v2(layout).startswith("# Omega Absorb Package Layout v2")
    contract = build_report_bundle_contract()
    assert "status" in contract.required_reports
    assert render_report_bundle_contract(contract).startswith("# Report Bundle Contract")


def test_workflow_and_command_groups():
    seed = build_workflow_seed()
    assert seed.steps
    assert render_workflow_seed(seed).startswith("# Workflow Seed")
    groups = build_cli_command_groups()
    assert groups.groups
    assert any(group.name == "os" for group in groups.groups)
    assert render_cli_command_groups(groups).startswith("# Omega Absorb CLI Command Groups")


def test_omega_absorb_os_v2_summary():
    os = build_omega_absorb_os_v2()
    assert os.version == "2.0.0"
    assert os.layout.sections
    assert os.command_groups.groups
    assert render_omega_absorb_os_v2(os).startswith("# Omega Absorb OS v2")
