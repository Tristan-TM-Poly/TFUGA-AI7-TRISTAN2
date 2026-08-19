from tools.organ_splitter import default_pr220_organs


def test_default_pr220_organs_has_expected_count():
    organs = default_pr220_organs()
    assert len(organs) == 12
    assert organs[0].organ_id == "organ_01"


def test_each_organ_has_required_parts():
    organ = default_pr220_organs()[0]
    assert "README" in organ.required_parts
    assert "tests" in organ.required_parts
    assert "oak_report" in organ.required_parts
