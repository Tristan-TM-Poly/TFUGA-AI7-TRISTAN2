from omega_info2 import InfoObject, InfoScores, OAKInfoGate, route_information
from omega_info2.github_issue_exporter import issue_draft_from_info_object


def test_issue_exporter_creates_non_mutating_draft_from_route():
    obj = InfoObject.example()
    obj.scores = InfoScores(
        truth=0.7,
        utility=0.9,
        fertility=0.9,
        testability=0.9,
        risk=0.2,
        source_trust=0.7,
    )
    OAKInfoGate().evaluate(obj)
    route_information(obj)
    draft = issue_draft_from_info_object(obj)
    payload = draft.to_dict()
    assert obj.id in payload["title"]
    assert "omega-info2" in payload["labels"]
    assert "OAK status" in payload["body"]
    assert "This issue draft does not assert truth" in payload["body"]
