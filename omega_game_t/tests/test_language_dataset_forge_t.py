from omega_game.engines import LanguageDataset, LanguageDatasetForge, default_language_dataset_forge


def test_dataset_forge_creates_requested_count():
    dataset = default_language_dataset_forge().forge(max_items=3)

    assert isinstance(dataset, LanguageDataset)
    assert len(dataset.items) == 3
    assert dataset.summary()["count"] == 3
    assert dataset.m_plus
    assert dataset.m_minus


def test_dataset_item_contract_and_scores():
    forge = LanguageDatasetForge()
    quest = forge.curriculum.quests_for_track("markdown_doc")[0]
    item = forge.forge_item(quest)
    payload = item.to_dict()

    assert set(payload) == {"item_id", "quest", "run", "evaluation", "validation", "repair", "tags", "score_summary"}
    assert 0.0 <= payload["score_summary"]["run_score"] <= 1.0
    assert 0.0 <= payload["score_summary"]["repair_score"] <= 1.0
    assert item.quest.track in item.tags


def test_dataset_summary_empty():
    dataset = default_language_dataset_forge().forge(max_items=0)

    assert dataset.summary() == {"name": "language_stack_dataset", "count": 0, "average_repair_score": 0.0, "converged": 0, "tracks": []}
    assert "empty_dataset" in dataset.m_minus


def test_dataset_forge_rejects_negative_max_items():
    try:
        default_language_dataset_forge().forge(max_items=-1)
    except ValueError as exc:
        assert "max_items" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_dataset_to_dict_contains_summary():
    dataset = default_language_dataset_forge().forge(max_items=2)
    payload = dataset.to_dict()

    assert set(payload) == {"name", "items", "summary", "m_plus", "m_minus"}
    assert payload["summary"]["count"] == 2
    assert len(payload["items"]) == 2


def test_dataset_tracks_are_sampled():
    dataset = default_language_dataset_forge().forge(max_items=9)
    tracks = dataset.summary()["tracks"]

    assert "fr_clear" in tracks
    assert "teaching" in tracks
    assert dataset.summary()["count"] == 9
