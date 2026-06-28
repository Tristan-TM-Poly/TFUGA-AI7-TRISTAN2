from omega_info2 import BayesTristanUpdater, BayesTristanVector, EvidenceVector, InfoObject, InfoScores


def test_bayes_tristan_truth_increases_with_supporting_evidence():
    prior = BayesTristanVector(truth=0.5, utility=0.5, fertility=0.5)
    report = BayesTristanUpdater().update(
        prior,
        [EvidenceVector(label="replicated benchmark", truth_lr=3.0, utility_lr=1.5, source="benchmark:001")],
    )
    assert report.posterior.truth > prior.truth
    assert report.posterior.utility > prior.utility
    assert not report.residue


def test_bayes_tristan_records_missing_evidence_source_residue():
    prior = BayesTristanVector(truth=0.5)
    report = BayesTristanUpdater().update(prior, [EvidenceVector(label="unsourced claim", truth_lr=2.0)])
    assert report.posterior.truth > prior.truth
    assert report.residue


def test_bayes_tristan_can_update_info_object_scores():
    obj = InfoObject.example()
    obj.scores = InfoScores(truth=0.4, utility=0.5, fertility=0.7, testability=0.6, risk=0.3)
    report = BayesTristanUpdater().update_info_object(
        obj,
        [EvidenceVector(label="counterexample", truth_lr=0.25, source="test:counterexample")],
    )
    assert obj.scores.truth == report.posterior.truth
    assert obj.scores.truth < 0.4
