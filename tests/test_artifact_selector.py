from tools.artifact_swarm import BranchNeed, choose_artifact


def test_basic_artifact_routes():
    assert choose_artifact(BranchNeed.IDEA_WITHOUT_PROOF).artifact == "test_tool.py"
    assert choose_artifact(BranchNeed.TOOL_WITHOUT_BENCHMARK).artifact == "benchmark.md"
    assert choose_artifact(BranchNeed.FERTILE_BRANCH).path_hint == "docs/roadmaps/"
