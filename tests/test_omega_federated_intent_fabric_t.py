from omega_federated_intent_fabric_t import (
    AuthorityLevel,
    FederatedIntentCompiler,
    IntentKind,
    RelationKind,
    SourceEnvelope,
    SourceKind,
    SourceVisibility,
)
from omega_federated_intent_fabric_t.model import SourceAvailability


def _github_source(**overrides):
    kwargs = dict(
        source_kind=SourceKind.GITHUB,
        source_id="Tristan-TM-Poly/example#1",
        fingerprint="sha256:abc",
        observed_at="2026-08-20T13:16:00-04:00",
        visibility=SourceVisibility.PUBLIC,
        availability=SourceAvailability.PRESENT,
        authority=AuthorityLevel.READ,
        provenance=("github:example#1",),
        claims=("the exact-head test suite passes",),
        explicit_intents=("Reuse existing intent compiler",),
        residuals=("cross-source provenance is not normalized",),
        prohibitions=("Do not authorize merge from generated intent",),
        metadata={"regenerable": "true"},
    )
    kwargs.update(overrides)
    return SourceEnvelope.build(**kwargs)


def test_compile_is_deterministic_and_never_authorizes_actions():
    compiler = FederatedIntentCompiler()
    source = _github_source()

    first = compiler.compile([source])
    second = compiler.compile([source])

    assert first.receipt_sha256 == second.receipt_sha256
    assert first.action_authorized is False
    assert all(intent.action_authorized is False for intent in first.intents)
    assert all(intent.status == "PROPOSED" for intent in first.intents)
    assert {intent.kind for intent in first.intents} == {
        IntentKind.EXPLICIT,
        IntentKind.VERIFICATION,
        IntentKind.COUNTER,
        IntentKind.RESIDUAL,
        IntentKind.NEGATIVE,
        IntentKind.REGENERATIVE,
    }


def test_claim_generates_verification_and_counter_intents_only_as_proposals():
    receipt = FederatedIntentCompiler().compile([_github_source()])
    texts = {intent.text for intent in receipt.intents}

    assert "Verify claim: the exact-head test suite passes" in texts
    assert "Falsify claim: the exact-head test suite passes" in texts
    assert receipt.action_authorized is False


def test_empty_source_becomes_reobservation_intent_not_negative_domain_claim():
    dropbox = SourceEnvelope.build(
        source_kind=SourceKind.DROPBOX,
        source_id="dropbox-root-scan",
        fingerprint="scan:empty",
        observed_at="2026-08-20T13:16:00-04:00",
        availability=SourceAvailability.EMPTY,
        authority=AuthorityLevel.READ,
    )

    receipt = FederatedIntentCompiler().compile([dropbox])

    assert receipt.empty_source_count == 1
    assert receipt.intent_count == 1
    assert receipt.intents[0].kind == IntentKind.VERIFICATION
    assert "Re-observe source availability" in receipt.intents[0].text
    assert not any(intent.kind == IntentKind.NEGATIVE for intent in receipt.intents)


def test_cross_source_exact_duplicate_is_relation_not_silent_merge():
    first = _github_source(
        source_id="repo-a#1",
        fingerprint="sha:a",
        claims=(),
        residuals=(),
        prohibitions=(),
        metadata={},
    )
    second = SourceEnvelope.build(
        source_kind=SourceKind.GOOGLE_DRIVE,
        source_id="doc-1",
        fingerprint="drive:1",
        observed_at="2026-08-20T13:16:00-04:00",
        explicit_intents=("Reuse existing intent compiler",),
        authority=AuthorityLevel.READ,
    )

    receipt = FederatedIntentCompiler().compile([first, second])

    duplicates = [relation for relation in receipt.relations if relation.kind == RelationKind.DUPLICATE]
    assert len(duplicates) == 1
    assert duplicates[0].inferred is True
    assert len(duplicates[0].intent_ids) == 2


def test_source_order_does_not_change_receipt():
    first = _github_source(source_id="repo-a#1", fingerprint="sha:a")
    second = SourceEnvelope.build(
        source_kind=SourceKind.GOOGLE_DRIVE,
        source_id="doc-1",
        fingerprint="drive:1",
        observed_at="2026-08-20T13:16:00-04:00",
        claims=("BOOK0 seed is sufficient for regeneration",),
        authority=AuthorityLevel.READ,
    )
    compiler = FederatedIntentCompiler()

    assert compiler.compile([first, second]).receipt_sha256 == compiler.compile([second, first]).receipt_sha256


def test_ucir_seed_preserves_authority_boundary():
    receipt = FederatedIntentCompiler().compile([_github_source()])
    seed = FederatedIntentCompiler.ucir_seed(receipt)

    assert seed["authority"]["generated_intents_authorized"] is False
    assert seed["authority"]["external_action_authorized"] is False
    assert seed["receipt_sha256"] == receipt.receipt_sha256


def test_duplicate_source_envelope_is_rejected():
    compiler = FederatedIntentCompiler()
    source = _github_source()

    try:
        compiler.compile([source, source])
    except ValueError as exc:
        assert "duplicate source envelope" in str(exc)
    else:
        raise AssertionError("duplicate source envelope must fail closed")
